import json

# This class is used to load and save persistent configuration settings,
# from both files and devices.
# Specify a filename if you want to load settings from a file
# Specify a message namespace that contains the following messages, if you want to set/get settings in a device:
#   GetConfigKeys       - get list of keys stored in a device
#   SetConfigValue      - set the value of a key
#   GetConfigValue      - get the value of a key
#   DeleteConfigValue   - delete a key's value
#   CurrentConfigKeys   - the current list of keys stored in a device
#   CurrentConfigValue  - the current value of a key stored in a device
# Specify a connection if you want to talk to a device.
# Example:
#     cfg_settings = ConfigSettings("autopilot.cfg", M.Messages.Autopilot, cxn)
#     cfg_settings.SaveToDevice()
class ConfigSettings:
    def __init__(self, filename=None, msg_namespace=None, connection=None):
        self.settings = {}
        if filename:
            self.LoadFromFile(filename)
        self.msg_namespace = msg_namespace
        self.connection = connection

    def SaveToFile(self, filename):
        with open(filename, 'w') as f:
            for key, value in self.settings.items():
                d = {key: value}
                f.write(json.dumps(d)+"\n")

    def LoadFromFile(self, filename):
        self.settings = {}
        with open(filename, 'r') as f:
            for line in f:
                data = json.loads(line)
                for key, values in data.items():
                    self.settings[key] = values

    def SaveToDevice(self):
        for key, values in self.settings.items():
            try:
                # If the value is an empty string, delete the setting from the device.
                if values == "":
                    msg = self.msg_namespace.DeleteConfigValue()
                    msg.SetKey(key)
                else:
                    msg = self.msg_namespace.SetConfigValue()
                    msg.SetKey(key)
                    idx = 0
                    for value in values.split(","):
                        msg.SetValues(float(value), idx)
                        idx += 1
                    msg.SetCount(idx)
                self.connection.send(msg)
            except KeyError:
                print("ERROR! Invalid Key %s not in %s" % (key, self.items_by_key.keys()))

    def LoadFromDevice(self):
        MAX_RETRIES = 10
        RX_TIMEOUT = 1.0 # floating point seconds
        keys_to_request = {}

        # Do a number of retries, for timing out on receiving messages
        for i in range(MAX_RETRIES):
            # Request the list of config keys
            query_msg = self.msg_namespace.GetConfigKeys()
            self.connection.send(query_msg)
            # wait for a response
            msg = self.connection.recv(self.msg_namespace.CurrentConfigKeys, RX_TIMEOUT)

            # if we got a message with a list of config setting keys,
            # iterate through the keys and add them to the dictionary
            # of keys to request values for.
            if type(msg) == self.msg_namespace.CurrentConfigKeys:
                for i in range(msg.GetCount()):
                    keys_to_request[msg.GetKey(i)] = True
                break

        # Do a number of retries, for timing out on receiving messages
        for i in range(MAX_RETRIES):
            # Request values for all the keys we haven't received values for yet.
            for key in keys_to_request.keys():
                query_msg = self.msg_namespace.GetConfigValue()
                query_msg.SetKey(key)
                self.connection.send(query_msg)

            # Loop as long as we keep receiving messages without a timeout occurring
            while True:
                msg = self.connection.recv(self.msg_namespace.CurrentConfigValue, RX_TIMEOUT)
                if type(msg) == self.msg_namespace.CurrentConfigValue:
                    # if we got a message with the value of a config setting,
                    # store it in the dictionary, unless it's an invalid key
                    key_int = msg.GetKey(enumAsInt=True)
                    key = msg.GetKey()
                    if key == "Invalid" or key_int == 0:
                        return
                    if key in keys_to_request:
                        del keys_to_request[key]
                        count = msg.GetCount()
                        value = ""
                        for i in range(count):
                            value += str(msg.GetValues(i)) + ", "
                        value = value[:-2]
                        self.settings[key] = value
                        if len(keys_to_request) == 0:
                            break
                    else:
                        print("Key %s not in keys %s" % (key, list(keys_to_request.keys())))
                elif msg == None:
                    # If we timed out, then break out of the rx loop into the timeout loop.
                    break
                else:
                    print("Received unexpected message %s" % (msg))
        return self.settings
    CPP_FILE_TEMPLATE = '''\
// AUTOGENERATED FILE, DO NOT HAND EDIT!
// created by <CMDLINE> at <DATETIME>
#include "config_settings.h"
#include "<MSG_HEADER_NAME>"

int DefaultConfigSetting::Count() { return <SETTINGS_COUNT>; }
ConfigSettings::ConfigSetting<ConfigSettings::MAX_LEN>** DefaultConfigSetting::Defaults()
{
<CONFIG_SETTINGS>
    static ConfigSettings::ConfigSetting<ConfigSettings::MAX_LEN>* defaults[] = {
<CONFIG_DECLS>
    };
    return defaults;
}
'''
    def SaveToCppFile(self, filename, msg_header_name, enum_prefix):
        import datetime
        import sys
        if enum_prefix:
            enum_prefix = "(int)"+enum_prefix
        cfg_settings = ""
        for key, value in self.settings.items():
            value = value.replace(",", "f,")+"f"
            length = value.count(",")+1
            crc = 0
            cfg_settings += "    static const ConfigSettings::ConfigSetting<%s> %s_setting = {%s/*crc*/, %s, %s-1/*size=len-1*/, {%s}};\n" % (length, key, crc, enum_prefix+key, length, value)
        cfg_decls = ""
        if len(self.settings) > 0:
            for key, value in self.settings.items():
                length = value.count(",")+1
                cfg_decls += "        {(ConfigSettings::ConfigSetting<ConfigSettings::MAX_LEN>*)&%s_setting},\n" % (key)
        else:
            cfg_decls += "        {0},\n"
        cfg_decls = cfg_decls[:-2]
        output = ConfigSettings.CPP_FILE_TEMPLATE
        output = output.replace("<CMDLINE>", " ".join(sys.argv[:]))
        output = output.replace("<DATETIME>", str(datetime.datetime.now()))
        output = output.replace("<SETTINGS_COUNT>", str(len(self.settings)))
        output = output.replace("<CONFIG_SETTINGS>", cfg_settings)
        output = output.replace("<CONFIG_DECLS>", cfg_decls)
        output = output.replace("<MSG_HEADER_NAME>", msg_header_name)
        with open(filename, 'w') as f:
            f.write(output)
