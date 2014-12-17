# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import pyqtSlot, pyqtSignal
import logging
logger = logging.getLogger(__name__)

class LabelExt(QtGui.QLabel):
    start_move_camera = pyqtSignal('QPoint')
    end_move_camera = pyqtSignal('QPoint')
    move_camera = pyqtSignal('QPoint')

    def __init__(self, parent=None):
        QtGui.QLabel.__init__(self, parent)
        self.setMouseTracking(False)
        self.s_pos = None
    
    def mouseMoveEvent(self, event):
        QtGui.QLabel.mouseMoveEvent(self, event)
        
        if self.s_pos is not None:
            self.move_camera.emit(event.pos() - self.s_pos)

    def mousePressEvent(self, event):
        QtGui.QLabel.mousePressEvent(self, event)
        
        if event.button() == QtCore.Qt.LeftButton:
            self.s_pos = event.pos()
            self.start_move_camera.emit(QtCore.QPoint(0,0))
    
    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.end_move_camera.emit(event.pos() - self.s_pos)
            self.s_pos = None
    
    def on_move_camera(self, pos):
        logger.debug("move_camera: {}".format(pos))

if __name__ == '__main__':
    from PyQt4 import QtGui
    from mainwindow import MainWindow
    import sys

    logging.basicConfig(filename='', level=logging.DEBUG)
    logging.getLogger("PyQt4").setLevel(logging.INFO)
    
    app = QtGui.QApplication(sys.argv)
    widget = LabelExt()
    widget.move_camera.connect(widget.on_move_camera)
    widget.show()
    sys.exit(app.exec_())  
