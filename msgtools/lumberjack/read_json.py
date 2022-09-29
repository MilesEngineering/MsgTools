#------------------------------------------------------------------------------
# This reads a JSON log file into a dictionary that for each message name, has
# a list of all the messages of that type, with each message as dictionary with
# attribute access.
#------------------------------------------------------------------------------
import json
import collections
import types

# this allows getting keys in two ways:
# d['key']
# d.key
class DictWithAttributeAccess(dict):
    def __getattr__(self, key):
        return self[key] 
    def __setattr__(self, key, value):
        self[key] = value

def split(filename):
    # this is a dictionary of all the message types, and each
    # value is a list of messages of that type.
    msgs = DictWithAttributeAccess()

    with open(filename, 'r') as f:
        # read a line at a time, and append each message to a list for that message
        for line in f:
            j = json.loads(line, object_hook = lambda dict: DictWithAttributeAccess(dict))
            for msgname, msg in j.items():
                safename = msgname.replace('.','_')
                if not safename in msgs:
                    msgs[safename] = []
                msgs[safename].append(msg)
    return msgs
