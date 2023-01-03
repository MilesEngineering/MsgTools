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
        dict_of_dataframes[msgname] = pd.DataFrame.from_records(dict_of_dataframes[msgname], index="Time")

    return dict_of_dataframes

class PandasBinaryReader(MessageFileReader):
    def __init__(self, filename, serial):
        super(PandasBinaryReader, self).__init__()
        self.dict_of_dataframes = {}
        header_name = "NetworkHeader"
        if serial:
            header_name = "SerialHeader"
        self.read_file(filename, header_name)

        for msgname in self.dict_of_dataframes:
            self.dict_of_dataframes[msgname] = pd.DataFrame.from_records(self.dict_of_dataframes[msgname], index="Time")
        

    def process_message(self, msg, timestamp):
        # Get a dictionary of the message
        d = msg.toDict(includeHeader=True)

        # the dictionary has one key, which is the name of the message
        msgname = list(d.keys())[0]

        # Within the value for that key, there's a "hdr", which contains "Time",
        # and we should override that with the corrected timestamp
        d[msgname]['hdr']['Time'] = timestamp

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
        from os import listdir
        from os.path import splitext, isfile, join
        def filename_is_log(filename):
            if not filename.startswith("20"):
                return False
            filename_elements = splitext(filename)
            if len(filename_elements) < 2:
                return False
            ext = filename_elements[1]
            if not ext in [".json", ".bin"]:
                return False
            return True
        filenames = [f for f in listdir(".") if isfile(f) and filename_is_log(f)]
        filenames.sort(reverse=True)
        filename = filenames[fileindex]

    global last_filename
    last_filename = filename

    if filename.endswith(".json"):
        return load_json(filename)
    elif filename.endswith(".bin") or filename.endswith(".log") or filename.endswith(".txt"):
        return load_binary(filename, serial)

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
