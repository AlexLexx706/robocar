# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import pyqtSlot
import logging

logger = logging.getLogger(__name__)

class SceneView(QtGui.QGraphicsView):
    def __init__(self, parent=None):
        super(QtGui.QGraphicsView, self).__init__(parent)
        self.setTransformationAnchor(QtGui.QGraphicsView.AnchorUnderMouse)
    
    def wheelEvent(self, event):
        scaleFactor = 1.15
        
        if event.delta() > 0:
            self.scale(scaleFactor, scaleFactor)
        else:
            self.scale(1.0 / scaleFactor, 1.0 / scaleFactor)