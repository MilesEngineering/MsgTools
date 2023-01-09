import copy
import gevent
from gevent.event import Event
import logging
import time

# This is used for formatting logging messages.
class StyleAdapter(logging.LoggerAdapter):
    def __init__(self, logger, sim):
        self.logger = logger
        self.sim = sim

    def log(self, level, msg, *args):
        if self.isEnabledFor(level):
            t = SimExec.time()
            self.logger._log(level, ("%7.3f: " % t) + msg, args, ())

# This class is used to execute a simulation, and allow tasks to be run along
# with it, at the appropriate simulation time rate.
# If no simulation exists, it falls back to using Python system time instead
# of simulation time.
class SimExec:
    # a gevent.event used to get coroutines to run when simulation time increases
    tick_event = None
    # a boolean to indicate if a simulation really exists.
    # if not, users probably want to use Python time instead of simulation time
    sim_exists = False
    allow_socket_comms = True
    _current_time = 0.0
    logging = StyleAdapter(logging.getLogger(__name__), None)
    def __init__(self, dt, args, logging):
        SimExec.tick_event = Event()
        self._args = args
        # If running ASAP, don't allow socket communications, because
        # it'd slow things down too much, and if any socket clients
        # were connected, they wouldn't be able to handle the flood of
        # messages.  ASAP is only good for batch processing with data
        # being written to files.
        if self._args.asap:
            SimExec.allow_socket_comms = False
        self.logging = logging
        SimExec.logging = logging
        self.dt = dt
        self.iterations_per_second = int(1/self.dt)
        self.start_time = time.time()
        self.last_time = self.start_time
        self.iterations = 0
        self.incremental_sim_time = 0
        self.incremental_wallclock_time = 0
        self.incremental_execution_time = 0

        # for lockstep mode
        self.ready_to_run = True

    @staticmethod
    def time():
        # Use SimExec.sim_exists to tell if a sim object exists, so we know if time
        # needs to sync to sim time, or if it should be free-running system time.
        if SimExec.sim_exists:
            return SimExec._current_time
        else:
            return time.time()

    # wait for some amount of simulation time (or real time, if sim not running)
    @staticmethod
    def wait(dt):
        # Use SimExec.sim_exists to tell if a sim object exists, so we know if time
        # needs to sync to sim time, or if it should be free-running system time.
        if SimExec.sim_exists:
            t1 = SimExec._current_time
            if dt > 0.0:
                while True:
                    SimExec.tick_event.wait()
                    SimExec.tick_event.clear()
                    t2 = SimExec._current_time
                    if t2 - t1 > dt:
                        break
                    #print("not yet")
            else:
                # sleep for zero time, to allow another coroutine to run
                gevent.sleep(0)
                t2 = SimExec._current_time
        else:
            t1 = time.time()
            #time.sleep(dt)
            # The Client implementation changed to always use greenlets, so we
            # should *always* do a gevent.sleep() here!
            # Undo this if the Client changes so that it doens't use greenlets
            # when SimExec.sim_exists is False!
            gevent.sleep(dt)
            t2 = time.time()
        SimExec.logging.debug("SimExec.wait(%.3f ms): %.3f ms" % (1000.0*dt, 1000.0*(t2-t1)))
        #print(f"{i} waited {dt} seconds")

    def time_tick(self, simtime):
        SimExec._current_time = simtime
        # perform a gevent Event set, to wake anything waiting on sim
        # time changing.
        SimExec.tick_event.set()
        now = time.time()
        actual_dt = now - self.last_time
        self.iterations += 1
        self.incremental_sim_time += self.dt
        if self._args.asap:
            self.incremental_wallclock_time += actual_dt
            if self.iterations % self.iterations_per_second == 0:
                self.logging.info("simtime %.1f / walltime %.3f = %.1fx acceleration" % (self.incremental_sim_time, self.incremental_wallclock_time, self.incremental_sim_time/self.incremental_wallclock_time))
                self.incremental_sim_time = 0.0
                self.incremental_wallclock_time = 0.0
            # do zero-time sleep, so other coroutines can run if they had yielded
            gevent.sleep(0)
            self.last_time = now
        else:
            self.incremental_execution_time += (now-self.last_time)
            sleep_time = self.dt - actual_dt
            self.logging.log(logging.ERROR if sleep_time < 0.25 * self.dt else logging.DEBUG, "Execution took %f seconds, want to run every %f seconds, sleeping %f seconds" % (actual_dt, self.dt, sleep_time))
            if self.iterations % self.iterations_per_second == 0:
                self.logging.warning("cputime %.3f / walltime %.1f = %.2f%% processor usage" % (self.incremental_execution_time, self.incremental_sim_time, 100.0*(self.incremental_execution_time/self.incremental_sim_time)))
                self.incremental_sim_time = 0.0
                self.incremental_wallclock_time = 0.0
                self.incremental_execution_time = 0.0
            if self.dt > actual_dt:
                gevent.sleep(sleep_time)
            else:
                # do zero-time sleep, so other coroutines can run if they had yielded
                gevent.sleep(0)
            self.last_time = time.time()
