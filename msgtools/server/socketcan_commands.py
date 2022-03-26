import can
import os
from PyQt5 import QtCore

class SocketcanCommands(QtCore.QObject):
    statusUpdate = QtCore.pyqtSignal(str)
    portsChanged = QtCore.pyqtSignal()
    def __init__(self, parent):
        super().__init__(parent)
        self._process = QtCore.QProcess(self)
        self._process.setProcessChannelMode(QtCore.QProcess.MergedChannels)
        self._process.readyReadStandardOutput.connect(self._printStdOut)
    
    # Adding a destructor does no good, it doesn't seem to get run (which is a known issue with Python).
    # Instead our stop() function below must be called when our parent's window closes.
    #def __del__(self):
    #    self.stop()

    def stop(self):
        if self._process.state() == QtCore.QProcess.Running:
            # closing the write channel seems to make the 'pkexec sh' exit.
            # trying to send ctrl-d to it, or calling terminate on the process, don't seem to work.
            self._process.closeWriteChannel()
            self._process.waitForFinished( 500 )
        if self._process.state() == QtCore.QProcess.Running:
            self.statusUpdate.emit("ERROR!  SocketcanCommands QProcess still running!")
            self._process.kill()

    def list(self):
        return can.detect_available_configs(['socketcan', "pcan"])
    
    def create(self, name):
        # Create the virtual CAN interface.
        self._run_command('ip link add dev %s type vcan' % name)
        self._run_command('ip link set %s up' % name)

    def configure(self, name, bitrate=1e6, data_bitrate=5e6):
        # configure
        self._run_command('ip link set %s down' % name)
        self._run_command('ip link set %s type can bitrate %d dbitrate %d fd on' % (name, bitrate, data_bitrate))
        self._run_command('ip link set %s up' % name)

    def delete(self, name):
        # bring down
        self._run_command('ip link del %s' % name)

    def _run_command(self, command):
        if self._process.state() == QtCore.QProcess.NotRunning:
            self._process.start('pkexec', ["sh"])
            self._process.waitForStarted()
        self._process.write(str.encode("echo %s\n%s\n" % (command,command), encoding='utf-8'))

    def _printStdOut(self):
        sender = self.sender()
        output = str(sender.readAllStandardOutput(), encoding='utf-8')
        # remove blank lines
        output = os.linesep.join([s for s in output.splitlines() if s])
        if output != "":
            self.statusUpdate.emit("socketcan: %s" % output)
        self.portsChanged.emit()

