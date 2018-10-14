from datetime import datetime
import inspect
import sys
import traceback
import signal

def trace_lines(frame, event, arg):
    """Handler that executes with every line of code"""

    # We only care about *line* and *return* events
    if event != 'line' and event != 'return':
        return

    # Get a reference to the code object and source
    co = frame.f_code
    #source = inspect.getsourcelines(co)[0]

    # Send the UI information on the code we're currently executing
    trace_lines.applicationq.put(
        {"co": {"file": co.co_filename,
                "name": co.co_name,
                "lineno": frame.f_lineno},
         #"frame": {"lineno": frame.f_lineno,
         #          "firstlineno": co.co_firstlineno,
         #          "locals": str(frame.f_locals),
         #          "source": source},
         'trace': 'line'})

    # Wait for a debug command
    cmd = trace_lines.debugq.get()

    if cmd == "step":
        # If stepping through code, return this handler
        return trace_lines

    elif cmd == 'over':
        # If stepping over, then return nothing, unless we're at top level
        if co.co_name == "<module>":
            return trace_lines
        # If stepping out of code, return the function callback
        return trace_calls

    # print("CODE")
    # print("co_argcount " + str(co.co_argcount))
    # print("co_cellvars " + str(co.co_cellvars))
    # print("co_code " + str(co.co_code))
    # print("co_consts " + str(co.co_consts))
    # print("co_filename " + str(co.co_filename))
    # print("co_firstlineno " + str(co.co_firstlineno))
    # print("co_flags " + str(co.co_flags))
    # print("co_freevars " + str(co.co_freevars))
    # print("co_kwonlyargcount " + str(co.co_kwonlyargcount))
    # print("co_lnotab " + str(co.co_lnotab))
    # print("co_name " + str(co.co_name))
    # print("co_names " + str(co.co_names))
    # print("co_nlocals " + str(co.co_nlocals))
    # print("co_stacksize " + str(co.co_stacksize))
    # print("co_varnames " + str(co.co_varnames))
    #
    # print("FRAME")
    # print("clear " + str(frame.clear))
    # # print("f_back " + str(frame.f_back))
    # # print("f_builtins " + str(frame.f_builtins))
    # # print("f_code " + str(frame.f_code))
    # # print("f_globals " + str(frame.f_globals))
    # print("f_lasti " + str(frame.f_lasti))
    # print("f_lineno " + str(frame.f_lineno))
    # print("f_locals " + str(frame.f_locals))
    # print("f_trace " + str(frame.f_trace))

def trace_calls(frame, event, arg):
    """Handler that executes on every invocation of a function call"""

    # We only care about function call events
    if event != 'call':
        return

    # Get a reference for the code object and function name
    co = frame.f_code

    #TODO: If filename doesn't match, maybe still handle stepping,
    # as long as its source we might want to debug?
    if co.co_filename == trace_lines.debug_filename:
        # Get the source code from the code object
        #print("filename: " + co.co_filename)
        #source = inspect.getsourcelines(co)[0]

        # Tell the UI to perform an update
        trace_lines.applicationq.put(
            { "co": {"file": co.co_filename,
                      "name": co.co_name,
                      "lineno": frame.f_lineno},
              #"frame": {"lineno": frame.f_lineno,
              #          "firstlineno": co.co_firstlineno,
              #          "locals": str(frame.f_locals),
              #          "source": source},
              "trace": "call"})

        # Wait for a debug command (we stop here right before stepping into or out of a function)
        cmd = trace_lines.debugq.get()

        if cmd == 'step':
            # If stepping into the function, return the line callback
            return trace_lines
        elif cmd == 'over':
            # If stepping over, then return nothing, unless we're at top level
            if co.co_name == "<module>":
                return trace_lines
            return

    return

class stdout_capture:
    def write(self, data):
        trace_lines.applicationq.put({'stdout': data})
class stderr_capture:
    def write(self, data):
        trace_lines.applicationq.put({'stderr': data})

sout = stdout_capture()
serr = stderr_capture()

def exit_gracefully(signum, frame):
    exit()

def debug(applicationq, debugq, filename):
    """Sets up and starts the debugger"""

    # Setup the debug and application queues as properties of the trace_lines functions
    trace_lines.debugq = debugq
    trace_lines.applicationq = applicationq
    trace_lines.debug_filename = filename

    # capture output, to send to the applicationq
    sys.stdout = sout
    sys.stderr = serr

    # Enable debugging by setting the callback
    sys.settrace(trace_calls)
    
    # try to exit gracefully
    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)

    # Execute the function we want to debug with its parameters
    name = filename.replace("/", "_")
    import importlib
    try:
        module = importlib.machinery.SourceFileLoader(name, filename).load_module(name)
        print("Finished")
        trace_lines.applicationq.put({'exit': True})
    except SystemExit:
        print("Stopped")
        trace_lines.applicationq.put({'error': True})
    except:
        trace_lines.applicationq.put({'error': True})
        etype, value, tb = sys.exc_info()
        exc = ''.join(traceback.format_exception(etype, value, tb))
        trace_lines.applicationq.put({'exception': exc})
        #trace_lines.applicationq.put({'exception': {'type': str(etype), 'value': str(value), 'traceback': str(tb)}})
