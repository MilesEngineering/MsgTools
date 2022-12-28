import copy
import datetime
import fileinput
import gevent
import importlib
import json
import logging
import os
import signal
import sys

from msgtools.console.client import Client
from msgtools.lib.messaging import Messaging
from msgtools.sim.sim_exec import SimExec, StyleAdapter
from msgtools.lib.message import Message

# Script files can have blank lines and comments (started with #)
# Commands within them are of the form:
# [dt] cmd [option]
# where dt is optional, and "option" is required for some but not all commands.
# If dt is present, the script line execution will not occur until dt seconds have
# elapsed since the previous script line execution.
class ScriptReader:
    # This is the count of how many options each command has.
    # Any commands in the script file that are not in the dict below will cause
    # the sim to exit with an error message.
    OPTION_COUNT_OF_CMD = {"exit": 0, "send": 1, "delay": 1, "sleep": 1, "set": 1, "load": 1}
    class Line:
        def __init__(self, next_line, file, logging):
            next_line = next_line.strip()
            self.lineinfo = "%s:%d [%s]" % (file.filename(), file.lineno(), next_line)

            # try splitting into three: DT CMD OPTION
            # if that fails, split into two: CMD OPTION
            next_index = 0
            try:
                parts = next_line.split(' ', maxsplit = 2)
                might_be_dt = parts[0]
                self.exec_time = float(might_be_dt)
                next_index += 1
            except ValueError:
                parts = next_line.split(' ', maxsplit = 1)
                self.exec_time = 0.0

            # try getting the command as lower case text
            try:
                self.command = parts[next_index].lower()
            except ValueError:
                logging.error("Error parsing %s, invalid command" % (self.lineinfo))
                exit(1)

            if not self.command in ScriptReader.OPTION_COUNT_OF_CMD.keys():
                logging.error("Invalid command [%s] in script line %s" % (self.command, self.lineinfo))
                exit(1)

            option_count = ScriptReader.OPTION_COUNT_OF_CMD[self.command]
            if option_count > 0:
                next_index += 1
                try:
                    self.option = parts[next_index]
                    if self.command in ["sleep", "delay"]:
                        if self.exec_time == 0.0:
                            self.exec_time = float(self.option)
                except IndexError:
                    logging.error("Error parsing %s, invalid options" % (self.lineinfo))
                    exit(1)

    def __init__(self, filename, start_time, logging):
        self.logging = logging
        # _script_files is a list, so we can have scripts load other scripts,
        # and when the child script is done, the parent script resumes.
        self._script_files = []
        self._script_files.append(fileinput.FileInput(filename))
        self._last_time = start_time
        self._read_line()

    def get_next_command(self, t):
        # return the next script input unless it's not time to send the next one
        while len(self._script_files)>0 and t >= self._line.exec_time:
            if self._line.command == "load":
                self.logging.warning("Loading script %s" % (self._line.option))
                self._script_files.append(fileinput.FileInput(self._line.option))
                self._read_line()
            else:
                ret = copy.deepcopy(self._line)
                self._read_line()
                return ret
        return None

    def _read_line(self):
        while 1:
            # when there's no files left, return
            if len(self._script_files) == 0:
                self._line = None
                return
            next_line = self._script_files[-1].readline()
            # When we get to the end of the file, pop it off the list
            if not next_line:
                self._script_files.pop()
                continue

            # if the line we read is blank or a comment, continue to the next line.
            if next_line.isspace():
                continue
            if next_line.startswith("#"):
                continue
            break
        # remove leading and trailing spaces, and then split on first space
        self._line = ScriptReader.Line(next_line, self._script_files[-1], self.logging)
        self._line.exec_time += self._last_time
        self._last_time = self._line.exec_time

# The sim base class executes a FDM (flight dynamics model), and optionally
# FSW (flight software), along with an optional test script (text based, or
# python).  The various entities are all run according to simulation time,
# and can pass messages amongst themselves and the network.
class SimBaseClass:
    def __init__(self, dt, fsw_dir, fsw_module, args):
        SimExec.sim_exists = True
        self._args = args
        logging.basicConfig(level=10*self._args.loglevel, format='')
        self.logging = StyleAdapter(logging.getLogger(__name__), self)
        self.time_stats = SimExec(dt, self._args, self.logging)
        self.cxn = Client('Sim', timeout=0.0)

        self.log_file_type = None
        self.log_file = None
        if self._args.log != None:
            if self._args.log == "":
                self._args.log = "json"
            self.start_log(self._args.log)

        # Open the initial script file
        if self._args.script != None:
            script_filename = self._args.script[0]
            if script_filename.endswith('.py'):
                script_args = self._args.script[1:]
                #print("script_args {%s}" % (script_args))
                # spawn the script using gevent
                spec = importlib.util.spec_from_file_location("sim.script", script_filename)
                sim_script = importlib.util.module_from_spec(spec)
                sys.modules["sim.script"] = sim_script
                spec.loader.exec_module(sim_script)

                #TODO does something need to join with this?!
                gevent.spawn(sim_script.main, *script_args)
                self.script_reader = None
            else:
                self.script_reader = ScriptReader(script_filename, self.get_time(), self.logging)
        else:
            self.script_reader = None

        if self._args.fsw:
            # go up until we find the FSW dir, then add it to the path, and
            # import the FSW module.
            search_dir = os.getcwd()
            while not os.path.isdir(os.path.join(search_dir, fsw_dir)):
                last_search_dir = search_dir
                search_dir = os.path.abspath(os.path.join(search_dir, os.pardir))
                if last_search_dir == search_dir:
                    exit("ERROR!  Cannot find FSW path %s upstream of %s" % (fsw_dir, os.getcwd()))
            fsw_dir = os.path.join(search_dir, fsw_dir)
            self.logging.info("Adding %s for path, to import FSW python module" % (fsw_dir))
            sys.path.append(fsw_dir)
            self.fsw = importlib.import_module(fsw_module)
        else:
            self.fsw = None

        gevent.signal_handler(signal.SIGTERM, SimBaseClass.close, signal.SIGTERM)
        gevent.signal_handler(signal.SIGINT, SimBaseClass.close, signal.SIGINT)

    @staticmethod
    def close(signo):
        sys.exit('\n%s received - aborting.' % (str(signo)))

    @staticmethod
    def setup_args(parser):
        parser.add_argument('--lockstep', action='store_true', help='Set if you want sim and FSW to run in lockstep.')
        parser.add_argument('--asap', action='store_true', help='Set if you want sim and FSW to run in lockstep, and as fast as possible (no sleep).')
        parser.add_argument('--loglevel', default="2", type=int, help='Set to how verbose of debug info you want printed. 0=none, 1=more, 2=even more, etc.')
        parser.add_argument('--script', default=None, nargs='+', help="Filename to load for scripted actions, and command-line arguments to give to the script.")
        parser.add_argument('--log', nargs='?', const='', help='The log file type (csv/json/bin) or complete log file name.  Can use strftime formatting for datetime, and a "+" is replaced with "%%Y%%m%%d_%%H%%M%%S"')

    def start_log(self, log_name):
        if log_name.endswith('csv'):
            self.log_file_type = "csv"
            # hash table of booleans for if each type of message has had it's header
            # put into this log file already.
            self._logged_msg_header_row = {}
        elif log_name.endswith('json'):
            self.log_file_type = "json"
        elif log_name.endswith('bin') or log_name.endswith('log'):
            self.log_file_type = "bin"
        else:
            self.logging.error("ERROR!  Invalid log type " + log_name)
        
        if log_name in ["csv","json","bin","log"]:
            # if they *only* supplied a suffix, assume they want the default datetime format string
            log_file_name = "%Y%m%d_%H%M%S" + "." + self.log_file_type
        else:
            # if they supplied more than just a suffix, then assume they named it the way they want.
            log_file_name = log_name
        log_file_name = log_file_name.replace("+", "%Y%m%d_%H%M%S")
        # if not, generate a filename based on current date/time
        now = datetime.datetime.now()
        log_file_name = now.strftime(log_file_name)
        if self.log_file_type == "bin":
            self.log_file = open(log_file_name, "wb")
        else:
            self.log_file = open(log_file_name, "w")

    def log(self, msg):
        if self.log_file:
            # if the message doesn't have a time set, set it to current sim time.
            if msg.hdr.GetTime() == 0.0:
                msg.hdr.SetTime(self.get_time())

            if self.log_file_type == "json":
                txt = msg.toJson(includeHeader=True) + "\n"
            elif self.log_file_type == "csv":
                txt = ""
                if not msg.MsgName() in self._logged_msg_header_row:
                    self._logged_msg_header_row[msg.MsgName()] = True
                    txt = msg.csvHeader(timeColumn=True)+'\n'
                txt += msg.toCsv(timeColumn=True) + "\n"
            elif self.log_file_type == "bin":
                txt = msg.rawBuffer().raw
            self.log_file.write(txt)

    def process_script_inputs(self):
        while self.script_reader:
            # round time up a smidge to account for floating-point inaccuracies, so
            # that if there's times that print like 4.00000 but are actually 3.999999999,
            # they happen when sim time is 4, and not when it's 4.050
            rounded_time = self.get_time() + self.time_stats.dt/2
            script_line = self.script_reader.get_next_command(rounded_time)
            if script_line == None:
                return

            if script_line.command == "set":
                #TODO: We need to add the ability to override values in a simulation variable database.
                #TODO: These values could be data that the sim is using to construct and send
                #TODO: messages on a regular basis, such that the script can specify values for them,
                #TODO: that are then incorporated into what the sim outputs.
                #TODO: They can also be any other variables that the sim wants to use for any purpose:
                #TODO: some could be just flags to script changing sim behaviour, others could be numerical
                #TODO: values that are nominally inputs to the sim, others could be values used to control
                #TODO: hardware in the lab (ie: power supply voltage, DAC outputs, wind models).
                # It'd be nice to handle JSON here so you could specify the root of a sim variable database branch like:
                # simdb.gps.pos {"lat": 42, "lon": 37, "alt": 12345}
                # instead of having to set the variables separately.
                # after setting values (to JSON for a branch, or just one value for a leaf), we want to be able to
                # restore the ability for the sim to compute values again, with some syntax, maybe this:
                # 0 set simdb.gps.pos UNLOCK
                # ^ That will, for the given branch, iterate over all the leaves under it, and set a flag that lets the sim compute values for them
                pass
            elif script_line.command == "send":
                #TODO: This constructs and sends a message, which is certainly a thing we want the capability to do!
                try:
                    msg = Message.fromJson(script_line.option)
                    # what to do with message?
                    # give it to FSW, or Sim, or both?!?
                    self.logging.warning("Script input %s" % (script_line.lineinfo))
                    self.send(msg, None)
                except json.decoder.JSONDecodeError:
                    self.logging.error("Script ERROR! Ignoring invalid JSON %s" % (script_line.lineinfo))
                    exit(1)
            elif script_line.command == "sleep" or script_line.command == "delay":
                # Nothing to do here, because we already delayed for the sleep/delay, as part of
                # how we handle all script commands
                self.logging.warning("Script %s until %f" % (script_line.command, script_line.exec_time))
            elif script_line.command.startswith("--"):
                # Set command line arguments in the _args structure.
                # Note that this will only change the value, it will not invoke any special handling
                # for the argument that might occur on startup.  If you do want special handling to
                # occur, the code should be restructured so there's a function that gets executed
                # when arguments are set, and that function should be called here as well as on startup.
                command = script_line.command.replace("--","")
                if command in dir(self._args):
                    arg = getattr(self._args, command)
                    if type(arg) == bool:
                        bool_value = not script_line.option.lower() in ['false', '0']
                        self.logging.info("Script %s bool_value: %s = %s" % (command, script_line.option, str(bool_value)))
                        setattr(self._args, command, bool_value)
                    elif type(arg) == float:
                        float_value = float(script_line.option)
                        self.logging.info("Script %s float_value: %s = %s" % (command, script_line.option, str(float_value)))
                        setattr(self._args, command, float_value)
                    elif type(arg) == int:
                        int_value = int(script_line.option)
                        self.logging.info("%s int_value: %s = %s" % (command, script_line.option, str(int_value)))
                        setattr(self._args, command, int_value)
                    else:
                        setattr(self._args, command, script_line.option)
                        print(type(arg))
                        print(dir(arg))
                else:
                    self.logging.error("ERROR! No valid command-line option %s" % command)
                    exit(1)
            elif script_line.command == "exit":
                self.logging.error("Exiting because %s" % (script_line.lineinfo))
                exit(1)
            else:
                # Should add handling of other script commands like:
                # 1) Changing simulation variables to be dynamically calculated vs. set from the script
                #    This would be used so you can temporarily override a value, and then go back to letting the sim calculate it.
                #    Ideally we'd want to be able to set sim variables to functions like a ramp between values over a time period, a sine wave with constants A,B,C for s = A * sin(B*time) + C, etc.
                # 2) Testing conditions of simulation variables being an exact match, within a range, below a min, or above a max.
                #    This would be used to make automated tests decide pass/fail criteria, and log the result to an output file
                # 3) Prompt the user to perform an action
                # 4) Pause or resume running (do we pause physics, execution, or both?)  AviSim would pause physics but not execution, that would horribly confuse an autopilot (integrator windup!)
                # 5) Sleep/Delay script processing for a certain amount of time.  This is in contrast to current behaviour where all lines have a delta T to delay as their first param
                self.logging.error("Unrecognized script command %s" % (script_line.lineinfo))

    def run(self):
        while True:
            self.process_script_inputs()
            self.get_commands()
            
            if self._args.lockstep:
                if not self.time_stats.ready_to_run:
                    continue
                self.time_stats.ready_to_run = False
            
            # execute the sim for one time step
            self.fdm.run()
            
            # Send tick to FSW, to allow it to run in sync with sim.
            self.output_time_tick()

            # run flight software, if it exists
            if self.fsw:
                self.fsw.run()

            # send aircraft state
            self.output_aircraft_state()

            # sleep until time to run again
            self.time_stats.time_tick(self.get_time())

    #TODO This is messy, and might be simplified by creating two Client
    # objects, one for FSW and one for FDM.  Client already passes messages
    # between instances of itself, so it might eliminate some of the logic
    # here and in recv().
    def send(self, msg, sender=None):
        # set time, if it's not already set
        if msg.hdr.GetTime() == 0.0:
            msg.hdr.SetTime(self.get_time())
        # log the message
        self.log(msg)

        # give the message to whoever didn't send it

        if sender != self.fdm:
            # if it's for setting a sim value, set the value
            #TODO: This should be modified to set things either within the self.fdm[] object, or outside it
            #TODO: and we should be able to override sim values temporarily, and restore them to letting the sim calculate them.
            #TODO: Maybe that means we should require the string to start with "fdm." if it's for the flight dynamics model,
            #TODO: and otherwise make it be treated like a "normal" simulation variable (which doesn't exist yet)
            if type(msg) == Messaging.Messages.Hitl.SetSimValue:
                self.logging.warning("Setting %s = %f" % (msg.GetVariableName(), msg.Value))
                self.fdm[msg.GetVariableName()] = msg.Value

        if self.fsw and sender != self.fsw:
            self.fsw.send(msg.rawBuffer().raw)

        # Also give the message to the network, if it's connected
        if self.cxn:
            try:
                ret = self.cxn.send(msg)
            except (BrokenPipeError, ConnectionResetError):
                self.cxn = None

    def recv(self):
        # if there's any messages from flight software, return them,
        # but also send them to the network
        if self.fsw:
            msgbuf = self.fsw.recv()
            if msgbuf:
                hdr = Messaging.hdr(messageBuffer=msgbuf)
                msg = Messaging.MsgFactory(hdr)
                self.log(msg)
                if self.cxn:
                    try:
                        self.cxn.send(msg)
                    except (BrokenPipeError, ConnectionResetError):
                        self.cxn = None
                return msg
        # if there's any messages from the network, return them,
        # but also send them to flight software
        if self.cxn:
            try:
                msg = self.cxn.recv()
                if msg:
                    self.log(msg)
                    if self.fsw:
                        self.fsw.send(msg.rawBuffer().raw)
                    return msg
            except (BrokenPipeError, ConnectionResetError):
                self.cxn = None
        # since nothing returned above, return None to indicate no messages.
        return None

    def process_sim_command(self, msg):
        if type(msg) == Messaging.Messages.TimeTock:
            self.time_stats.ready_to_run = True

    def get_commands(self):
        while True:
            msg = self.recv()
            if msg == None:
                self.logging.debug("No messages read, are you sure FSW is running?")
                break
            self.process_sim_command(msg)

    def output_time_tick(self):
        if self._args.lockstep or self._args.fsw:
            simtime = self.get_time()
            tick = Messaging.Messages.TimeTick()
            tick.Time = simtime
            self.send(tick, self.fdm)
