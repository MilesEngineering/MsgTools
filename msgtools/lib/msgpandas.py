#!/usr/bin/env python3
import json
import pandas as pd
import time
from collections import OrderedDict

from msgtools.lib.file_reader import MessageFileReader
from msgtools.lib.messaging import Messaging

# function to flatten a dictionary of a Message object, according to
# some unique properties of Message objects.
def flatten_msg(msg):
    out = {}

    def flatten(x, name=''):
        if type(x) is dict or type(x) is OrderedDict:
            for a in x:
                # leave the header as a dictionary, otherwise it's a lot of clutter
                if name == '' and a == "hdr":
                    #print(name+a)
                    # Put the whole header in the output
                    #out[name+a] = x[a]

                    # make other hdr fields a regular field
                    for field in x[a].keys():
                        if "time" in field.lower():
                            out[name+field] = x[a][field]
                        elif field in ["ID", "DataLength"]:
                            pass
                        elif field in ["Source", "Destination"]:
                            if x[a][field] != 0:
                                out[name+field] = x[a][field]
                else:
                    flatten(x[a], name + a + '.')
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name[:-1] + "["+str(i) + '].') # extra . will be removed by next call to flatten()
                i += 1
        else:
            out[name[:-1]] = x

    flatten(msg)
    return out

def load_json(filename):
    dict_of_dataframes = {}

    with open(filename) as f:
        for line in f:
            j = json.loads(line)
            for msgname in j.keys():
                # "flat" is a dictionary, but not nested!
                flat = flatten_msg(j[msgname])

                # add to dictionary of dataframes
                if not msgname in dict_of_dataframes:
                    dict_of_dataframes[msgname] = []
                dict_of_dataframes[msgname].append(flat)

    for msgname in dict_of_dataframes:
        if "FIELD_METADATA." in msgname:
            # message metadata, occurs only once for each message type, with no time tag.
            dict_of_dataframes[msgname] = pd.DataFrame.from_records(dict_of_dataframes[msgname], index="name")
        else:
            # normal messages, with time-tagged data
            dict_of_dataframes[msgname] = pd.DataFrame.from_records(dict_of_dataframes[msgname], index="Time")

    return dict_of_dataframes

class PandasBinaryReader(MessageFileReader):
    def __init__(self, filename, serial):
        super(PandasBinaryReader, self).__init__()
        self.dict_of_dataframes = {}
        header_name = None
        if serial:
            header_name = "SerialHeader"
        self.read_file(filename, header_name)

        for msgname in self.dict_of_dataframes:
            self.dict_of_dataframes[msgname] = pd.DataFrame.from_records(self.dict_of_dataframes[msgname], index="Time")
        

    def process_message(self, msg):
        # Get a dictionary of the message
        d = msg.toDict(includeHeader=True)

        # the dictionary has one key, which is the name of the message
        msgname = list(d.keys())[0]

        flat = flatten_msg(d[msgname])

        # add to dictionary of dataframes
        if not msgname in self.dict_of_dataframes:
            self.dict_of_dataframes[msgname] = []
        self.dict_of_dataframes[msgname].append(flat)

def load_binary(filename, serial=None):
    # if user didn't specify value for serial, set it based on filename.
    if serial == None:
        if filename.endswith(".bin") or filename.endswith(".log"):
            serial = False
        elif filename.endswith(".txt"):
            serial = True

    # Need to read binary messages and process them.
    # flatten_msg() above was written to operate on python dicts returned
    # by reading JSON.  The Message class already overloads the __getattr__()
    # function to make field access work like attribute access, and perhaps
    # if we also override __dir__(), then Message objects could be operated
    # on like python objects with named attributes.  If that doesn't work,
    # we can either change flatten_msg() to work on Message objects, using their
    # normal means of reflection, or generate JSON and then parse the JSON to
    # form a dictionary, and then call flatten_msg() on that dictionary.
    pandas_reader = PandasBinaryReader(filename, serial)

    return pandas_reader.dict_of_dataframes

def field_units(dict_of_dataframes, msgname, fieldname):
    return dict_of_dataframes["FIELD_METADATA."+msgname].loc[fieldname]["units"]

# Make a subclass of pandas.DataFrame that doesn't raise exceptions when
# plot is called, even if there's no data to plot.
class DataFrameSubclass(pd.DataFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field_metadata = None
    def plot(self, *args, **kwargs):
        # Build a mapping for how to rename columns to include units
        rename_with_units = {}
        for c in self.columns.values:
            units = self.field_metadata.loc[c]["units"]
            if units != "":
                rename_with_units[c] = "%s (%s)" % (c, units)

        # Plot the columns, with the new column names that include units.
        try:
            super().rename(columns=rename_with_units).plot(*args, **kwargs)
        except TypeError:
            # If there's nothing to plot, print a message instead of crashing.
            print("Not plotting %s%s, nothing to plot!" % (self.msgname, self.columns.values))

# Make a subclass of dict that has a function that returns an empty dataframe
# if there's no matching dataframe with the specified keys.
class DataFrameDict(dict):
    def data(self, msgname, fieldnames):
        try:
            msg_dataframe = self[msgname]
        except KeyError:
            print("ERROR! [%s][%s] not in dataframe!" % (msgname, fieldnames))
            ret = DataFrameSubclass(columns=fieldnames)
            ret.msgname = msgname
            return ret
        
        # if we didn't hit the exception to return an empty DataFrameSubclass,
        # return a DataFrameSubclass of the dataframe we care about, but add
        # some extra members to it to access field metadata from the dataframe
        # dictionary.
        ret = DataFrameSubclass(msg_dataframe[fieldnames])
        ret.field_metadata = self["FIELD_METADATA."+msgname]
        return ret

    def field_units(self, msgname, fieldname):
        return self["FIELD_METADATA."+msgname].loc[fieldname]["units"]

# A global variable for the last filename that was loaded.
# This is useful for when None is passed in to load(),
# and the user wants to know what file was auto-loaded.
last_filename = None

# Return a hashtable of pandas dataframes from the file that was loaded.
def load(filename=None, serial=None):
    # if the filename was an int, use it as an index into the list of files,
    # and reset filename to None.  If filename was a valid file name, then
    # the cast to int will raise an exception and filename won't be reset.
    fileindex = 0
    try:
        fileindex = int(filename)
        filename = None
    except:
        pass
    if filename == None:
        import os, re
        def filename_is_log(filename):
            if not os.path.isfile(filename):
                return False
            # the filename should contain something that looks like YYYYMMDD in it
            if not re.search(pattern=r'20\d{6}[-_]\d{6}', string=filename):
                return False
            filename_elements = os.path.splitext(filename)
            if len(filename_elements) < 2:
                return False
            ext = filename_elements[1]
            if not ext in [".json", ".bin", ".log"]:
                return False
            return True
        def log_files(dir):
            return [dir+"/"+f for f in os.listdir(dir) if filename_is_log(dir+"/"+f)]
        def timestring(filename):
            return re.search(pattern=r'20\d{6}[-_]\d{6}', string=filename).group()
        # Get log files in current dir
        filenames = log_files(".")
        # add log files in logs subdir, if it exists
        try:
            filenames += log_files("logs")
        except FileNotFoundError:
            pass
        # sort by the timestring that was found in the filename
        filenames.sort(reverse=True, key=lambda x: timestring(x))
        filename = filenames[fileindex]

    global last_filename
    last_filename = filename

    if filename.endswith(".json"):
        ret = load_json(filename)
    elif filename.endswith(".bin") or filename.endswith(".log") or filename.endswith(".txt"):
        ret = load_binary(filename, serial)
    
    return DataFrameDict(ret)

# Make this script executable from the shell, with command line arguments.
# This is just for testing, since there's not much point in printing a DataFrame
# to stdout.
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Read a log file into pandas DataFrames")
    parser.add_argument('filename', nargs="?", default=None, help='''The log file you want to split into CSV.  
        .log extension assumes the log is binary with NetworkHeaders.  A .txt extension assumes the 
        file was created with SerialHeaders.''')
    parser.add_argument('--serial', action='store_true', help='''Assumes input file contains binary messages with SerialHeaders instead of NetworkHeaders.''')
    args = parser.parse_args()

    if args.filename and args.filename.lower().endswith('.txt'):
        args.serial = True
    
    df = load(args.filename, args.serial)
    print(df)

# main starts here
if __name__ == '__main__':
    main()
