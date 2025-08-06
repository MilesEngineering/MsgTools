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
            try:
                units = self.field_metadata.loc[c]["units"]
            except AttributeError:
                print("ERROR! No metadata for %s" % c)
            else:
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
        try:
            ret.field_metadata = self["FIELD_METADATA."+msgname]
        except KeyError:
            pass
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

def merge(message_fields, dfs, interpolate_first_column = False):
    """
    Construct a pandas dataframe based on data for message fields that exist in a
    dictionary of data frames with a dict key of message name and column of field
    name.
    
    The output dataframe will have a column for each message field.
    By default there will be a row for only timestamps that exist for the first
    message field specified, but the user can specify interpolate_first_column
    to be True if they want rows for every timestamp that exists in *any* of
    the columns we care about.

    For any timestamps that we provide output for, if a data point doesn't exist
    for a particular column, that row's column data will be filled by
    interpolated data, assuming linear change between neighboring timestamps.
    """

    # Find the name of the first field the user specified.
    # By default, we'll only generate output data that exists at timestamps
    # of the first field.
    first_arg = message_fields[0].split("=")
    first_msg = first_arg[0]
    first_field = first_arg[1]
    first_column_name = first_msg+'.'+first_field
    
    # Create a new dataframe for output that has only the data from the first field.
    df_out = dfs[first_msg][[first_field]].rename(columns={first_field: first_column_name})
    
    # Loop through all the subsequent fields and add them to the output dataframe,
    # but only for timestamps that we consider valid (by default, timestamps of
    # the first field).  Interpolate the data to fill gaps when it doesn't have
    # a value for a timestamp we care about.
    for message_field in message_fields[1:]: 
        argComponentList = message_field.split("=")
        next_msg = argComponentList[0]
        next_field = argComponentList[1]
        next_column = next_msg+'.'+next_field

        # Do an outer join of the next column into the dataframe.
        # This will add rows that exist in either the existing table or the new
        # column, and it'll put NaN into columns that don't exist at that Index
        # (ie: timestamp) for the row.
        df_out = df_out.join(dfs[next_msg][[next_field]],rsuffix=next_column, how="outer").rename(columns={next_field: next_column})

        # Interpolate *only* the field we just added.  We definitely don't want to interpolate the first column
        # unless the user had specified that option, and we don't want to waste time by calling interpolate
        # on all the columns we already interpolated.
        df_out[next_column] = df_out[next_column].interpolate(method='index')
    
        # After we interpolate data for the new column, decide what to do with rows that
        # don't have valid data in the first column. By default we'll remove them, unless
        # the caller specified interpolate_first_column to be True
        if interpolate_first_column:
            # Interpolate the first column.  This will result the output
            # dataframe having a row for any timestamp that occurs in
            # any column we're merging, not just for the timestamps of
            # the first column!
            df_out[first_column_name] = df_out[first_column_name].interpolate(method='index')
        else:
            # Drop any rows that have the first column as a NaN, because we only want rows
            # that have valid data for the first column.
            df_out.dropna(subset=[first_column_name], inplace=True)

    return df_out

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

    if args.filename:
        if args.filename and args.filename.lower().endswith('.txt'):
            args.serial = True
        
        df = load(args.filename, args.serial)
        print(df)
    else:
        test_merge()

def test_merge():
    import pandas as pd
    import matplotlib.pyplot as plt

    # Print help message 
    print(merge.__doc__)

    # Make fake data
    dfs = {}
    dfs['Msg1'] = pd.DataFrame.from_records(
        [{"Time": 0.0,  "FieldA": 0.0},
         {"Time": 0.1,  "FieldA": 0.1},
         {"Time": 0.2,  "FieldA": 0.2},
         {"Time": 0.3,  "FieldA": 0.3},
         {"Time": 0.4,  "FieldA": 0.4},
         {"Time": 2.0,  "FieldA": 2.0},
         {"Time": 2.01, "FieldA": 2.01},
         {"Time": 2.02, "FieldA": 2.02},
         {"Time": 2.03, "FieldA": 2.03},
         {"Time": 3.0,  "FieldA": 3.0}], index="Time")
    dfs['Msg2'] = pd.DataFrame.from_records(
        [{"Time": 0.0,  "FieldB": 0.0, "FieldC": 1.0},
         {"Time": 2.1,  "FieldB": 21.0,"FieldC": 3.1},
         {"Time": 3.0,  "FieldB": 30.0,"FieldC": 10.0}], index="Time")
    # Merge it!
    # Note that we're leaving out interpolate_first_column, but if you specify
    # that is true, then the merged data will have a row for any timestamp that
    # occurs in *any* column, not just the first!
    merged = merge(message_fields=["Msg1=FieldA", "Msg2=FieldB", "Msg2=FieldC"], dfs=dfs) #, interpolate_first_column=True)

    # Print it
    print(dfs)
    print(merged)

    # Plot it
    fig, axes = plt.subplots(nrows=1, ncols=2, tight_layout=True)
    axes[0].set_title('Inputs')
    dfs['Msg1'].plot(ax=axes[0], marker=".")
    dfs['Msg2'].plot(ax=axes[0], marker=".")
    axes[1].set_title('Merged')
    merged.plot(ax=axes[1], marker=".")
    plt.show()

# main starts here
if __name__ == '__main__':
    main()
