import json
import pandas as pd
import time

# function to flatten a dictionary of a Message object, according to
# some unique properties of Message objects.
def flatten_msg(msg):
    out = {}

    def flatten(x, name=''):
        if type(x) is dict:
            for a in x:
                # leave the header as a dict, otherwise it's a lot of clutter
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

def load(filename):
    dict_of_dataframes = {}

    with open(filename) as f:
        for line in f:
            j = json.loads(line)
            for msgname in j.keys():
                # "flat" is a dict, but not nested!
                flat = flatten_msg(j[msgname])

                # add to dict of dataframes
                if not msgname in dict_of_dataframes:
                    dict_of_dataframes[msgname] = []
                dict_of_dataframes[msgname].append(flat)

    for msgname in dict_of_dataframes:
        dict_of_dataframes[msgname] = pd.DataFrame.from_records(dict_of_dataframes[msgname], index="Time")

    return dict_of_dataframes
