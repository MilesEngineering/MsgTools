#!/usr/bin/env python3
import argparse
import json
import os
import sys
import time
from .pytimedinput import GetKey

# if started via invoking this file directly (like would happen with source sitting on disk),
# insert our relative msgtools root dir into the sys.path, so *our* msgtools is used, not
# any other already in the path.
if __name__ == '__main__':
    srcroot=os.path.abspath(os.path.dirname(os.path.abspath(__file__))+"/../..")
    sys.path.insert(1, srcroot)

from msgtools.lib.file_reader import MessageFileReader
from msgtools.lib.messaging import Messaging
import msgtools.lib.msgcsv as msgcsv
import msgtools.lib.msgjson as msgjson
from msgtools.console.client import Client

DESCRIPTION='''
    msgreplay plays back recorded messages.
'''
class Replay(MessageFileReader):
    def __init__(self):
        super(Replay, self).__init__()

        parser = argparse.ArgumentParser(description=DESCRIPTION)
        parser.add_argument('logfile', help='''The log file you want to play back.  
            .bin or .log extension assumes the log is binary.
            .json assumes the log file is JSON.''')
        parser.add_argument('--speed', type=float, default="1.0", help='''Speed.  Less than 1 to slow down, greater than 1 to speed up.''')
        parser.add_argument('-i', '--include', nargs='+', help='''A list of message names to exclude from replay.''')
        parser.add_argument('-e', '--exclude', nargs='+', help='''A list of message names to exclude from replay.''')
        parser.add_argument('--debug', action='store_true', help='''Set to get more debug info.''')
        parser.add_argument('--ignoreinvalid', nargs='?', default=False, help='''Set to ignore invalid messages and fields in the log file.''')
        parser.add_argument('--newtime', action='store_true', help='''Set new timestamps in the messages we replay.  Default is to use original timestamps.''')
        self.args = parser.parse_args()

        # Open a client connection to replay the messages on
        self.connection = Client("Replay")

        # Figure out what to include/exclude
        self.excluded_msgs = None
        if self.args.exclude:
            if self.args.debug:
                print("Excluding %s" % (self.args.exclude))
            self.excluded_msgs = {}
            for msg_name in self.args.exclude:
                msg_id = self.msgid_from_name(msg_name)
                self.excluded_msgs[msg_id] = True
            if self.args.debug:
                print("Excluded: %s" % (list(self.excluded_msgs.keys())))
        self.included_msgs = None
        if self.args.include:
            if self.args.debug:
                print("Including %s" % (self.args.include))
            self.included_msgs = {}
            for msg_name in self.args.include:
                msg_id = self.msgid_from_name(msg_name)
                self.included_msgs[msg_id] = True
            if self.args.debug:
                print("Included: %s" % (list(self.included_msgs.keys())))
        self.message_sent_count = 0
        self.message_skipped_count = 0
        self.total_message_sent_count = 0
        self.total_message_skipped_count = 0
        
        time_units = Messaging.hdr.GetTime.units
        if time_units == "ms":
            self.time_scale = 1.0e-3
        elif time_units == "us":
            self.time_scale = 1.0e-6
        elif time_units == "ns":
            self.time_scale = 1.0e-9
        elif time_units == "s":
            self.time_scale = 1.0
        else:
            print("Invalid time units %s in Message header, exiting." % (time_units))
            exit(1)

        self.last_msg_time = None
        self.last_time = time.time()
        print("Press space or p to pause, f to speed up, s to slow down, ctrl-c to quit")
        try:
            if self.args.ignoreinvalid != None:
                # If it's not none, set the value the user passed in
                ignore_invalid = self.args.ignoreinvalid
            else:
                # If the arg is None, the user used the option, but didn't specify a value, so use true.
                ignore_invalid = True
            self.read_file(self.args.logfile, "NetworkHeader", ignore_invalid=ignore_invalid)
        except KeyError as e:
            print("\n\nKeyError!\nRe-run with --ignoreinvalid or --ignoreinvalid=silent if you want to ignore these!\n")
            raise e
        except KeyboardInterrupt:
            pass
        print("\nFinal Log time %.3f: replayed %d, skipped %d" % (self.last_msg_time, self.total_message_sent_count, self.total_message_skipped_count))

    def msgid_from_name(self, msg_name):
        try:
            msg_id = int(msg_name)
            return msg_id
        except:
            pass
        try:
            msg_class = Messaging.MsgClassFromName[msg_name]
            id = msg_class.ID
            return id
        except KeyError:
            print("ERROR!  Invalid message name " + msg_name)
            if self.args.debug:
                print("not in: %s" % ("\n".join(list(Messaging.MsgClassFromName.keys()))))
            quit()


    def process_message(self, msg):
        id = msg.hdr.GetMessageID()

        if self.excluded_msgs:
            if id in self.excluded_msgs:
                self.message_skipped_count += 1
                return
        if self.included_msgs:
            if not id in self.included_msgs:
                self.message_skipped_count += 1
                return
        
        msg_time = msg.hdr.GetTime() * self.time_scale
        if self.args.newtime:
            msg.hdr.SetTime(currenttime() / self.time_scale)
        
        def do_speeds(user_key):
            if user_key == 'f':
                self.args.speed *= 2
                print("  Speeding up to speed %s" % (self.args.speed))
            elif user_key == 's':
                self.args.speed /= 2
                print("  Slowing down to speed %s" % (self.args.speed))
            
        if self.last_msg_time == None:
            self.last_msg_time = msg_time
        else:
            delta_time = (msg_time - self.last_msg_time) / self.args.speed
            if delta_time <= 0.0:
                pass
            else:
                user_key = GetKey(allowCharacters=" sfp", timeout=delta_time)
                if user_key != None:
                    if user_key in [' ','p']:
                        while True:
                            print("  Paused!  Press space or p to un-pause, f to speed up, s to slow down, ctrl-c to quit")
                            user_key = GetKey(allowCharacters=" sfp", timeout=10)
                            if user_key != None:
                                do_speeds(user_key)
                                break
                    else:
                        do_speeds(user_key)
                self.last_msg_time = msg_time
        self.message_sent_count += 1
        self.connection.send(msg)
        current_time = time.time()
        if current_time > self.last_time + 1.0:
            self.last_time = current_time
            skipped_str = ", skipped %d" % self.message_skipped_count if self.message_skipped_count else ""
            print("Log time %.3f: Replayed %d%s" % (self.last_msg_time, self.message_sent_count, skipped_str))
            self.total_message_sent_count += self.message_sent_count
            self.total_message_skipped_count += self.message_skipped_count
            self.message_sent_count=0
            self.message_skipped_count=0

def main():
    replay = Replay()

# main starts here
if __name__ == '__main__':
    main()
