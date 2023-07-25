from msgtools.lib.message import Message
from msgtools.lib.messaging import Messaging
from msgtools.lib.header_translator import HeaderHelper, HeaderTranslator
import ctypes
import importlib
import json
import math

class MessageFileReader:
    def __init__(self):
        # to handle timestamp wrapping
        self._timestampOffset = 0
        self._lastTimestamp = 0

    def error_fn(self, str):
        print(str)

    def read_file(self, filename, header_name, ignore_invalid=False):
        # load the messages if not already loaded
        if Messaging.hdr == None:
            try:
                if header_name != None:
                    Messaging.LoadAllMessages(headerName=header_name)
                else:
                    Messaging.LoadAllMessages()
            except RuntimeError as e:
                print(e)
                quit()
            except:
                import traceback
                print(traceback.format_exc())
                quit()

        # find the specific header used in the log, and create a translator
        # between that and regular messages.
        if header_name != None and header_name != Messaging.hdr.__name__:
            header_module = importlib.import_module("headers." + header_name)
            self.log_header = getattr(header_module, header_name)
            self.header_translator = HeaderTranslator(self.log_header, Messaging.hdr)
        else:
            self.log_header = Messaging.hdr
            self.header_translator = None
        self.header_helper = HeaderHelper(self.log_header, self.error_fn)

        if filename.endswith(".json"):
            self.read_json_file(filename, ignore_invalid)
        else:
            self.read_binary_file(filename)

    def read_binary_file(self, filename):
        with open(filename, mode='rb') as f:
            while(1):
                # If we need to translate the header, then read the header and body separately.
                # Otherwise do a single big read and seek backwards for the next message's start, because that is ~10% faster.
                if self.header_translator:
                    # read bytes, create a header
                    msg_bytes = f.read(self.log_header.SIZE)
                    if len(msg_bytes) < self.log_header.SIZE:
                        break
                    hdr = self.log_header(msg_bytes)

                    if not self.header_helper.header_valid(hdr):
                        print("Invalid header!")
                        break

                    # read the body
                    msg_body = f.read(hdr.GetDataLength())

                    #if not self.header_helper.body_valid(hdr, msg.rawBuffer()[self.log_header.SIZE:]):
                    if not self.header_helper.body_valid(hdr, msg_body):
                        print("Invalid body!")
                        break

                    network_msg = self.header_translator.translateHdrAndBody(hdr, msg_body)
                else:
                    # <- read a kB of data so we do fewer (but larger) reads
                    last_header_pos = f.tell()
                    msg_bytes = ctypes.create_string_buffer(Messaging.hdr.SIZE+1024)
                    length_read = f.readinto(msg_bytes)
                    # Construct a header object
                    hdr = Messaging.hdr(msg_bytes)

                    if length_read < Messaging.hdr.SIZE:
                        break

                    if not self.header_helper.header_valid(hdr):
                        print("Invalid header!")
                        break

                    # <- seek back to just after the last message's data (where the next header starts)
                    f.seek(last_header_pos+Messaging.hdr.SIZE+hdr.GetDataLength())

                    hdr = Messaging.hdr(msg_bytes)

                    if not self.header_helper.body_valid(hdr, hdr.rawBuffer()[Messaging.hdr.SIZE:]):
                        print("Invalid body!")
                        break
                    
                    network_msg = hdr
                
                # Get a specifically typed message, to give to process_msg
                msg = Messaging.MsgFactory(network_msg)
                self.process_message(msg)

    def read_json_file(self, filename, ignore_invalid=False):
        with open(filename) as f:
            for line in f:
                msg = Message.fromJson(line, ignore_invalid)
                self.process_message(msg)
