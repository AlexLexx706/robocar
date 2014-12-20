#!/usr/bin/python 
# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import pyqtSlot, pyqtSignal
from cross_detector.ffmpeg_reader import FFmpegReader
from cross_detector.cross_detector import CrossDetector
import logging
import threading
import os
from video_view import VideoView
from tcp_rpc.client import Client
import numpy as np


logger = logging.getLogger(__name__)

class VideoFrame(QtGui.QFrame):
    new_video_frame = pyqtSignal(object)
    
    def __init__(self, settings):
        QtGui.QFrame.__init__(self)
        uic.loadUi(os.path.join(os.path.split(__file__)[0], "video_frame.ui"), self)
        self.settings = settings
        self.video_view = VideoView(self)
        self.verticalLayout_2.addWidget(self.video_view)

        self.video_thread = None
        self.new_video_frame.connect(self.on_new_video_frame)

    def start(self):
        if self.video_thread is None:
            self.video_thread = threading.Thread(target=self.read_frame)
            self.video_thread.start()
    
    def stop(self):
        if self.video_thread is not None:
            self.reader.release()
            self.video_thread.join()
            self.video_thread = None
            self.video_view.set_image(QtGui.QImage(":/res/Video.png"))
            
    def read_frame(self):
        '''Поток чтения данных с камеры'''
        self.reader = FFmpegReader()
        cross_detector = CrossDetector(False, self.reader)
        self.reader.process_net_stream(self.spinBox_port.value())
        host = self.settings.value("lidar_host", "192.168.0.91").toString()
        port = self.settings.value("lidar_port", 8080).toInt()[0]
        
        Client([host, port]).start_video_broadcasting(self.spinBox_port.value(), self.spinBox_w.value(), self.spinBox_h.value(), self.spinBox_fps.value())

        while 1:
            data = self.reader.read_string()
            l = len(data)
            if l == 0:
                break

            if l == self.reader.size[0] * self.reader.size[1] * 3:
                cross_detector.process(self.reader.to_frame(data))

                image = QtGui.QImage(data, self.reader.size[0], self.reader.size[1], self.reader.size[0] * 3, QtGui.QImage.Format_RGB888)
                self.new_video_frame.emit((image, cross_detector.get_marker_state()))
        
        Client([host, port]).stop_video_broadcasting()

    @pyqtSlot(bool)
    def on_pushButton_start_video_clicked(self, v):
        if self.video_thread is not None:
            self.stop()
            self.pushButton_start_video.setText(u"Запустить видео")
        else:
            self.start()
            self.pushButton_start_video.setText(u"Остановить видео")

    def on_new_video_frame(self, data):
        image, cross = data
        self.video_view.set_cross(cross)
        self.video_view.set_image(image)

    def closeEvent(self, event):
        self.stop()
        QtGui.QFrame.closeEvent(self, event)
