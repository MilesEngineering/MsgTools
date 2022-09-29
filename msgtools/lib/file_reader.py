from msgtools.lib.messaging import Messaging
from msgtools.lib.header_translator import HeaderHelper
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
                msg_bytes = f.read(Messaging.hdr.SIZE)
                if len(msg_bytes) < Messaging.hdr.SIZE:
                    break
                hdr = Messaging.hdr(msg_bytes)

                if not self.header_helper.header_valid(hdr):
                    print("Invalid header!")
                    break

                msg_bytes += f.read(hdr.GetDataLength())
                hdr = Messaging.hdr(msg_bytes)
                msg = Messaging.MsgFactory(hdr)
                #if not self.header_helper.body_valid(hdr, msg.rawBuffer()[Messaging.hdr.SIZE:]):
                if not self.header_helper.msg_valid(msg):
                    print("Invalid body!")
                    break

                self.setup_message(msg)

    def setup_message(self, msg):
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

        self.process_message(msg, timestamp)
