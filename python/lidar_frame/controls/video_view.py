# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import pyqtSlot, pyqtSignal
import logging

logger = logging.getLogger(__name__)

class VideoView(QtGui.QFrame):
    CROSS_RECT_SIZE = 20
    start_move_camera = pyqtSignal('QPoint')
    end_move_camera = pyqtSignal('QPoint')
    move_camera = pyqtSignal('QPoint')

    def __init__(self, parent=None):
        QtGui.QFrame.__init__(self, parent)
        self.setMouseTracking(False)
        self.s_pos = None
        self.image = None
        self.cross = None
        self.set_image(QtGui.QImage(":/res/video.png"))
        self.set_cross({"color": "white",
                         "center":(0.3,0.7)})
    
    def mouseMoveEvent(self, event):
        if self.s_pos is not None:
            print "self.move_camera.emit"
            self.move_camera.emit(event.pos() - self.s_pos)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.s_pos = event.pos()
            print "presss:", event.button()
            self.start_move_camera.emit(QtCore.QPoint(0,0))
    
    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            print "presss:", event.button()
            self.end_move_camera.emit(event.pos() - self.s_pos)
            self.s_pos = None
    
    def on_move_camera(self, pos):
        logger.debug("move_camera: {}".format(pos))

    def set_image(self, image):
        self.image = image
        self.update()

    def set_cross(self, cross):
        self.cross = cross
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)

        if self.image is not None and not self.image.isNull():
            painter.setRenderHint(QtGui.QPainter.Antialiasing)

            #отображение картинки
            new_size = self.image.size()
            new_size.scale(self.size(), QtCore.Qt.KeepAspectRatio)
            x = (self.width() - new_size.width()) / 2 if new_size.width() != self.width() else 0
            y = (self.height() - new_size.height()) / 2 if new_size.height() != self.height() else 0
            target = QtCore.QRect(x, y, new_size.width(), new_size.height())
            painter.drawImage(target, self.image, self.image.rect())

            #отображение креста
            self.draw_cross(painter, target)
        else:
            painter.fillRect(event.rect(), QtGui.QBrush(QtCore.Qt.white))

    def draw_cross(self, painter, target):
        if self.cross:
            painter.setPen(QtGui.QPen(QtCore.Qt.red))

            hs = self.CROSS_RECT_SIZE / 2.0
            x = target.x() + target.width()  * self.cross["center"][0] - hs
            y = target.y() + target.height()  * self.cross["center"][1] - hs
            rect = QtCore.QRectF(x, y, self.CROSS_RECT_SIZE, self.CROSS_RECT_SIZE)

            if self.cross["color"] == "white":
                painter.setBrush(QtGui.QBrush(QtCore.Qt.white))
            else:
                painter.setBrush(QtGui.QBrush(QtCore.Qt.black))
            painter.drawEllipse(rect)


if __name__ == '__main__':
    from PyQt4 import QtGui
    from mainwindow import MainWindow
    import sys

    logging.basicConfig(filename='', level=logging.DEBUG)
    logging.getLogger("PyQt4").setLevel(logging.INFO)
    
    app = QtGui.QApplication(sys.argv)
    widget = VideoView()
    widget.move_camera.connect(widget.on_move_camera)
    widget.show()
    sys.exit(app.exec_())  
