from msgtools.lib.messaging import Messaging
from msgtools.lib.header_translator import HeaderHelper
import ctypes
import math

class MessageFileReader:
    def __init__(self):
        # to handle timestamp wrapping
        self._timestampOffset = 0
        self._lastTimestamp = 0

    def error_fn(self, str):
        print(str)

    def read_file(self, filename, header_name):
        try:
            Messaging.LoadAllMessages(headerName=header_name)
        except RuntimeError as e:
            print(e)
            quit()
        except:
            import traceback
            print(traceback.format_exc())
            quit()

        self.header_helper = HeaderHelper(Messaging.hdr, self.error_fn)

        with open(filename, mode='rb') as f:
            while(1):
                # Below are three versions of accomplishing the same thing.
                # Each is faster but perhaps less straightforward than the previous.
                # The last one is about 10% faster than the first one.
                # For the purpose of constructing Pandas DataFrames, all methods are
                # slower than reading a JSON file
                if 0: # <- read bytes, create a header
                    msg_bytes = f.read(Messaging.hdr.SIZE)
                    if len(msg_bytes) < Messaging.hdr.SIZE:
                        break
                    hdr = Messaging.hdr(msg_bytes)
                elif 0: # <- read into a header object
                    last_header_pos = f.tell()
                    hdr = Messaging.hdr()
                    length_read = f.readinto(hdr.rawBuffer())
                    if length_read < Messaging.hdr.SIZE:
                        break
                else: # <- read a kB of data so we do fewer (but larger) reads
                    last_header_pos = f.tell()
                    msg_bytes = ctypes.create_string_buffer(Messaging.hdr.SIZE+1024)
                    length_read = f.readinto(msg_bytes)
                    #print("%d %d" % (last_header_pos, length_read))
                    hdr = Messaging.hdr(msg_bytes)
                    if length_read < Messaging.hdr.SIZE:
                        break

                if not self.header_helper.header_valid(hdr):
                    print("Invalid header!")
                    break

                if 0: # <- read more data for the body
                    msg_bytes += f.read(hdr.GetDataLength())
                elif 0: # <- seek back to before we read the header, make a new buffer, and read into it
                    f.seek(last_header_pos)
                    msg_bytes = ctypes.create_string_buffer(Messaging.hdr.SIZE+hdr.GetDataLength())
                    f.readinto(msg_bytes)
                else: # <- seek back to just after the last message's data (where the next header starts)
                    f.seek(last_header_pos+Messaging.hdr.SIZE+hdr.GetDataLength())
                hdr = Messaging.hdr(msg_bytes)
                msg = Messaging.MsgFactory(hdr)
                #if not self.header_helper.body_valid(hdr, msg.rawBuffer()[Messaging.hdr.SIZE:]):
                if not self.header_helper.msg_valid(msg):
                    print("Invalid body!")
                    break

                timestamp = self.timestamp(msg)
                self.process_message(msg, timestamp)

    def timestamp(self, msg):
        try:
            # \todo Detect time rolling.  this only matters when we're processing a log file
            # with insufficient timestamp size, such that time rolls over from a large number
            # to a small one, during the log.
            thisTimestamp = msg.hdr.GetTime()
            if thisTimestamp < self._lastTimestamp:
                self._timestampOffset+=1

            self._lastTimestamp = thisTimestamp

            maxTime = Messaging.findFieldInfo(msg.hdr.fields, "Time").maxVal
            if maxTime != 'DBL_MAX' and maxTime != 'FLT_MAX':
                timeSizeInBits = int(round(math.log(int(maxTime), 2)))
                timestamp = (self._timestampOffset << timeSizeInBits) + thisTimestamp
            else:
                timestamp = thisTimestamp
            if Messaging.findFieldInfo(msg.hdr.fields, "Time").units == "ms":
                timestamp = timestamp / 1000.0
        except AttributeError:
            timestamp = 0.0
        return timestamp
