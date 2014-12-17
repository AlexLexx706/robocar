#!/usr/bin/python 
# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import pyqtSlot, pyqtSignal
import logging
import threading
import math
import time
import pickle
import os
from tcp_rpc.client import Client
import Queue
from controls.alg_controls import AlgControls
from controls.sector_controls import SectorControls
from controls.data_view import DataView
from controls.video_frame import VideoFrame

logger = logging.getLogger(__name__)

class LidarFrame(QtGui.QFrame):
    new_data = pyqtSignal(object)
    
    def __init__(self, settings, parent=None, in_gueue_sector_data = None):
        QtGui.QFrame.__init__(self)
        uic.loadUi(os.path.join(os.path.split(__file__)[0], "lidar_frame.ui"), self)
        self.settings = settings
        
        self.sector_controls = SectorControls(settings)
        self.alg_controls = AlgControls(settings)
        
        self.tabWidget.addTab(self.sector_controls, u"Сектор")
        self.tabWidget.addTab(self.alg_controls, u"Алгоритм")
        
        self.data_view = DataView()
        self.video_frame = VideoFrame()
        
        self.splitter.addWidget(self.data_view)
        self.splitter.addWidget(self.video_frame)

        self.stop_flag = True
        self.new_data.connect(self.on_new_data)
        
        self.lineEdit_host.setText(self.settings.value("lidar_host", "192.168.0.91").toString())
        self.spinBox_port.setValue(self.settings.value("lidar_port", 8080).toInt()[0])
        self.lineEdit_file.setText(self.settings.value("lidar_file", "data.dat").toString())
        self.checkBox_step_mode.setChecked(self.settings.value("lidar_step_model", False).toBool())

        if self.settings.value("lidar_reader_type", 0).toInt()[0] == 0:
            self.radioButton_host.setChecked(True)
        else:
            self.radioButton_file.setChecked(True)
         
        self.write_file = None

        self.next_event = threading.Event()
        self.in_gueue_sector_data = in_gueue_sector_data
        self.label_frame.setText("0")
        self.frame_number = 0
        
        self.stop_record_flag = True
        self.record_lock = threading.Lock()

        if self.in_gueue_sector_data is not None:
            self.radioButton_queue.setEnabled(True)
            self.radioButton_queue.setChecked(True)
            self.start()
        else:
            self.radioButton_queue.setEnabled(False)
    
        self.readSettings()

    @pyqtSlot('QString')
    def on_lineEdit_host_textEdited(self, text):
        self.settings.setValue("lidar_host", text)

    @pyqtSlot('QString')
    def on_lineEdit_file_textEdited(self, text):
        self.settings.setValue("lidar_file", text)

    @pyqtSlot("int")
    def on_spinBox_port_valueChanged(self, value):
        self.settings.setValue("lidar_port", value)

    @pyqtSlot("bool")
    def on_toolButton_open_file_clicked(self, v):
        fileName = QtGui.QFileDialog.getOpenFileName(self, u"Открыть запись",
                                                 self.settings.value("lidar_file", "data.dat").toString(),
                                                 "Records (*.dat)")
        if len(fileName):
            self.lineEdit_file.setText(fileName)
            self.settings.setValue("lidar_file", fileName)


    @pyqtSlot(bool)
    def on_pushButton_play_clicked(self, v):
        if self.stop_flag:
            self.start()
        else:
            self.stop()

    @pyqtSlot(bool)
    def on_pushButton_next_clicked(self, v):
        if not self.stop_flag:
            self.next_event.set()

            if not self.checkBox_step_mode.isChecked():
                self.checkBox_step_mode.setChecked(True)

    @pyqtSlot(bool)
    def on_pushButton_record_clicked(self, v):
        if self.stop_record_flag:
            with self.record_lock:
                self.stop_record_flag = False
                self.record_list = []
            self.pushButton_record.setText(u"Закончить запись")
        else:
            with self.record_lock:
                self.stop_record_flag = True

            self.pushButton_record.setText(u"Начать запись")
            
            #Созранение в файл
            if len(self.record_list):
                fileName = QtGui.QFileDialog.getSaveFileName(self, u"Сохранить запись",
                                    self.settings.value("lidar_last_file", "data.dat").toString(),
                                    "Records (*.dat)")
                if len(fileName):
                    self.settings.setValue("lidar_last_file", fileName)
                    data_file = pickle.Pickler(open(unicode(fileName), "wb"))

                    for data in self.record_list:
                        data_file.dump(data)
    
    def add_record(self, data):
        with self.record_lock:
            if not self.stop_record_flag:
                self.record_list.append(data)

            
    
    @pyqtSlot(bool)
    def on_checkBox_step_mode_toggled(self, state):
        self.settings.setValue("lidar_step_model", state)

        if not state:
            self.next_event.set()
    
    @pyqtSlot(bool)
    def on_radioButton_host_toggled(self, v):
        if v:
            self.pushButton_record.setEnabled(True)
            self.settings.setValue("lidar_reader_type", 0)


    @pyqtSlot(bool)
    def on_radioButton_file_toggled(self, v):
        if v:
            self.pushButton_record.setEnabled(False)
            self.settings.setValue("lidar_reader_type", 1)

    @pyqtSlot(bool)
    def on_radioButton_queue_toggled(self, v):
        if v:
            self.pushButton_record.setEnabled(True)
        

    def on_new_data(self, data):
        self.label_frame.setText(str(data["frame_number"]))
        self.data_view.draw_data(data)

    def closeEvent(self, event):
        event.accept()
        self.writeSettings()


    def writeSettings(self):
        self.settings.beginGroup("windows_geometry")

        self.settings.beginGroup("lidar_frame")
        self.settings.setValue("splitter_2_sizes", self.splitter_2.sizes())
        self.settings.setValue("splitter_sizes", self.splitter.sizes())
        self.settings.endGroup()

        self.settings.endGroup()

    def readSettings(self):
        self.settings.beginGroup("windows_geometry")

        self.settings.beginGroup("lidar_frame")
        self.splitter_2.setSizes([int(v) for v in self.settings.value("splitter_2_sizes", [100, 100]).toPyObject()])
        self.splitter.setSizes([int(v) for v in self.settings.value("splitter_sizes", [100, 100]).toPyObject()])
        self.settings.endGroup()

        self.settings.endGroup()

    def start(self):
        if self.stop_flag:
            self.stop_flag = False
            self.frame_number = 0
            
            if self.radioButton_host.isChecked():
                self.read_thread = threading.Thread(target=self.read_server_proc)
            elif self.radioButton_file.isChecked():
                self.read_thread = threading.Thread(target=self.read_file_proc)
            elif self.radioButton_queue.isChecked():
                self.read_thread = threading.Thread(target=self.read_queue_proc)
                
            self.pushButton_play.setText(u"Стоп")
            self.frame_5.setDisabled(True)
            self.read_thread.start()
    
    def stop(self):
        if not self.stop_flag:
            self.stop_flag = True
            self.next_event.set()
            self.read_thread.join()
            self.pushButton_play.setText(u"Старт")
            self.frame_5.setDisabled(False)

    def wait_next_step(self):
        if self.checkBox_step_mode.isChecked():
            self.next_event.wait()
            self.next_event.clear()
            return True
        return False

    def read_server_proc(self):
        client = Client("{}:{}".format(unicode(self.lineEdit_host.text()), self.spinBox_port.value()), serialization="mesgpack")

        while not self.stop_flag:
            data = client.ik_get_sector(1)

            if data is not None:
                data = data[0]
                
                self.prepare_data({"sector": data})
                self.wait_next_step()

    def read_file_proc(self):
        if not os.path.exists(unicode(self.lineEdit_file.text())):
            return

        stream = pickle.Unpickler(open(unicode(self.lineEdit_file.text()), "rb"))

        while not self.stop_flag:
            try:
                data = stream.load()
                self.prepare_data({"sector": data})

                if not self.wait_next_step():
                    time.sleep(0.1)
            #конец файла
            except EOFError:
                stream = pickle.Unpickler(open(unicode(self.lineEdit_file.text()), "rb"))
                self.frame_number = 0
                time.sleep(1)

    def read_queue_proc(self):
        while not self.stop_flag:
            try:
                self.wait_next_step()
                data = self.in_gueue_sector_data.get(timeout=1)
            except Queue.Empty:
                continue

            if data is None:
                return

            self.prepare_data(data)

    def sector_2_primetives(self, data):
        primetives = self.sector_controls.draw_clusters(data)
        primetives.extend(self.alg_controls.draw_alg(data))
        return primetives

    @pyqtSlot(bool)
    def prepare_data(self, data):
        draw_data = {"frame_number": self.frame_number, "primetives": []}
        self.frame_number += 1

        #Обработка сектора
        if "sector" in data:
            draw_data["primetives"] = self.sector_2_primetives(data["sector"])
            self.add_record(data["sector"])
        
        if "primetives" in data:
            draw_data["primetives"].extend(data["primetives"])

        self.new_data.emit(draw_data)

       
def main(in_queue):
    import sys
    app = QtGui.QApplication(sys.argv)
    widget = LidarFrame(QtCore.QSettings("AlexLexx", "car_controlls"), in_gueue_sector_data=in_queue)
    widget.show()
    sys.exit(app.exec_())
        

if __name__ == '__main__':
    logging.basicConfig(filename='', level=logging.DEBUG)
    logging.getLogger("PyQt4").setLevel(logging.INFO)
    main(Queue.Queue(1))