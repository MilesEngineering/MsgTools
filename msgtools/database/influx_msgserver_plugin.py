from msgtools.database.influxdb import InfluxDBConnection
from msgtools.lib.messaging import Messaging
from PyQt5 import QtCore, QtGui, QtWidgets

class InfluxServerPlugin(QtCore.QObject):
    statusUpdate = QtCore.pyqtSignal(str)
    messagereceived = QtCore.pyqtSignal(object)
    disconnected = QtCore.pyqtSignal(object)

    def __init__(self, param):
        super(InfluxServerPlugin, self).__init__(None)
        
        # split up params, and use them to construct the DB connection.
        params = param.split("|")
        self.db = InfluxDBConnection(self, *params)

        # these are for interfacing to msgserver
        self.name = "InfluxDB"
        self.subscriptions = {}
        self.subMask = 0
        self.subValue = 0
        self.isHardwareLink = False
        self.statusLabel = QtWidgets.QLabel("influxdb %s:%d" % (self.db.hostname, self.db.port))

    def widget(self, index):
        if index == 0:
            return self.statusLabel
        return None

    def start(self):
        pass
    
    def stop(self):
        pass
    
    # for msgserver telling us to send
    def sendMsg(self, hdr):
        msg = Messaging.MsgFactory(hdr)
        self.db.handle_message(msg)
    
    # for influxdb telling us to send
    def send_message(self, hdr):
        self.messagereceived.emit(hdr)

def PluginConnection(param=""):
    isp = InfluxServerPlugin(param)
    return isp
