#!/usr/bin/env python3
"""
Plot message data in scrolling window
"""
#import initExample ## Add path to library (just for examples; you do not need this)

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np

pause = 0

class CustomViewBox(pg.ViewBox):
    def __init__(self, *args, **kwds):
        pg.ViewBox.__init__(self, *args, **kwds)
        
    def mouseClickEvent(self, ev):
        global pause
        if ev.button() == QtCore.Qt.LeftButton:
            pause = not pause

class MsgPlot:
    MAX_LENGTH = 100
    def __init__(self):
        self.win = pg.GraphicsWindow()
        self.win.setWindowTitle('pyqtgraph example: Scrolling Plots')

        vb = CustomViewBox()
        
        self.myPlot = self.win.addPlot(viewBox=vb)
        self.dataArray = []
        self.curve = self.myPlot.plot(self.dataArray)
        self.ptr1 = 0

    def addData(self, newDataPoint):
        # add data in the array until MAX_LENGTH is reached, then drop data off start of array
        # such that plot appears to scroll.  The array size is limited to MAX_LENGTH.
        if len(self.dataArray) >= MsgPlot.MAX_LENGTH:
            self.dataArray[:-1] = self.dataArray[1:]  # shift data in the array one sample left
            self.dataArray[-1] = newDataPoint
        else:
            self.dataArray.append(newDataPoint)

        global pause
        if not pause:
            self.ptr1 += 1
            self.curve.setData(self.dataArray)
            self.curve.setPos(self.ptr1, 0)

def onTimeout():
    msgPlot.addData(np.random.normal())

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys
    msgPlot = MsgPlot()
    
    timer = pg.QtCore.QTimer()
    timer.timeout.connect(onTimeout)
    timer.start(50)
    
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
