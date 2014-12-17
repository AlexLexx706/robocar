#!/usr/bin/python 
# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import pyqtSlot, pyqtSignal
from cross_detector.ffmpeg_reader import FFmpegReader
import logging
import threading
import os
from label_ext import LabelExt

logger = logging.getLogger(__name__)

class VideoFrame(QtGui.QFrame):
    new_video_frame = pyqtSignal("QImage")
    
    def __init__(self, *args):
        QtGui.QFrame.__init__(self, *args)
        uic.loadUi(os.path.join(os.path.split(__file__)[0], "video_frame.ui"), self)
        self.label_video = LabelExt(self)
        self.verticalLayout_2.addWidget(self.label_video)

        self.video_thread = None
        self.new_video_frame.connect(self.on_new_video_frame)

    def start(self):
        if self.video_thread is None:
            self.reader = FFmpegReader()
            self.video_thread = threading.Thread(target=self.read_frame)
            self.video_thread.start()
    
    def stop(self):
        if self.video_thread is not None:
            self.reader.release()
            self.video_thread.join()
            self.video_thread = None
            self.label_video.setPixmap(QtGui.QPixmap(":/res/Video.png"))
            
    def read_frame(self):
        '''Поток чтения данных с камеры'''
        self.reader.process_net_stream(5001)
        
        while 1:
            data = self.reader.read_string()
            l = len(data)

            if l == 0:
                break

            if l == self.reader.size[0] * self.reader.size[1] * 3:
                image = QtGui.QImage(data, self.reader.size[0], self.reader.size[1], self.reader.size[0] * 3, QtGui.QImage.Format_RGB888)
                self.new_video_frame.emit(image)

    @pyqtSlot(bool)
    def on_pushButton_start_video_clicked(self, v):
        if self.video_thread is not None:
            self.stop()
            self.pushButton_start_video.setText(u"Запустить видео")
        else:
            self.start()
            self.pushButton_start_video.setText(u"Остановить видео")

    def on_new_video_frame(self, image):
        self.label_video.setPixmap(QtGui.QPixmap.fromImage(image))

    def closeEvent(self, event):
        self.stop()
        QtGui.QFrame.closeEvent(self, event)
