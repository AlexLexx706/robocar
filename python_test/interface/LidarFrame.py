# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import pyqtSlot, pyqtSignal
import pyqtgraph as pg
import logging
import threading
import math
import time
import pickle
import os
from tcp_rpc.client import Client
from Vec2d import Vec2d
from LineFeaturesMaker import LineFeaturesMaker

logger = logging.getLogger(__name__)

class LidarFrame(QtGui.QFrame):
    new_data = pyqtSignal(object)
    
    def __init__(self, settings, parent=None):
        super(QtGui.QFrame, self).__init__(parent)
        uic.loadUi("LidarFrame.ui", self)
        self.settings = settings
                
        self.view = pg.GraphicsLayoutWidget()  ## GraphicsView with GraphicsLayout inserted by default
        self.view_layout.addWidget(self.view)
        self.stop_flag = True
        self.new_data.connect(self.on_new_data)
        self.lineEdit_host.setText(self.settings.value("lidar_host", "192.168.0.91").toString())
        self.spinBox_port.setValue(self.settings.value("lidar_port", 8080).toInt()[0])
        
        self.groupBox_connection.setChecked(self.settings.value("lidar_use_connection", True).toBool())
        self.checkBox_record.setChecked(self.settings.value("lidar_record", False).toBool())

        ## create four areas to add plots
        self.w1 = self.view.addPlot()
        self.w1.showGrid(x=True, y=True)
        self.w1.setAspectLocked()
        
        self.s1 = pg.ScatterPlotItem(size=5, pen=pg.mkPen(None), brush=pg.mkBrush(255, 255, 255, 120))
        self.w1.addItem(self.s1)
        self.write_file = None
        self.lfm = LineFeaturesMaker()


    def closeEvent(self, event):
        self.stop()
        QtGui.QFrame.closeEvent(self, event)
        
    
    @pyqtSlot()
    def on_lineEdit_host_editingFinished(self):
        self.settings.setValue("lidar_host", self.lineEdit_host.text())
    
    @pyqtSlot(int)
    def on_spinBox_port_valueChanged(self, value):
        self.settings.setValue("lidar_port", self.spinBox_port.value())
    
    @pyqtSlot(bool)
    def on_pushButton_control_clicked(self, v):
        if self.stop_flag:
            self.pushButton_control.setText(u"Стоп")
            self.start()
        else:
            self.pushButton_control.setText(u"Старт")
            self.stop()

    @pyqtSlot(bool)
    def on_groupBox_connection_clicked(self, v):
        self.settings.setValue("lidar_use_connection", v)
        
    @pyqtSlot(bool)
    def on_checkBox_record_toggled(self, v):
        self.settings.setValue("lidar_record", v)

    def start(self):
        url = (unicode(self.lineEdit_host.text()), self.spinBox_port.value())

        if self.stop_flag:
            self.stop_flag = False
            out_file = unicode(self.settings.value("lidar_record_file", "data.dat").toString())

            #запуск чтения с датчика
            if self.groupBox_connection.isChecked():
                self.read_thread = threading.Thread(target=self.read_proc, args=(url, out_file if self.checkBox_record.isChecked() else None))
            #запуск из файла
            else:
                self.read_thread = threading.Thread(target=self.read_file_proc, args=(out_file, ))
            self.read_thread.start()
    
    def stop(self):
        if not self.stop_flag:
            self.stop_flag = True
            self.read_thread.join()

    def read_proc(self, url, out_file):
        client = Client(url)
        
        #Создадим поток для записи данных
        if out_file is not None:
            out_file = pickle.Pickler(open(out_file, "wb"))

        while not self.stop_flag:
            data = client.ik_get_sector(1)

            if data is not None:
                data = data[0]
                print self.lfm.sector_to_lines(data)
                self.new_data.emit(self.lfm.sector_to_clusters(data))
                    
                #пишем поток.
                if out_file is not None:
                    out_file.dump(data)


    def read_file_proc(self, file_path):
        if not os.path.exists(file_path):
            return

        stream = pickle.Unpickler(open(file_path, "rb"))
       
        while not self.stop_flag:
            try:
                data = stream.load()
                self.new_data.emit(self.lfm.sector_to_clusters(data))
                time.sleep(1.0)
            #конец файла
            except EOFError:
                stream = pickle.Unpickler(open(file_path, "rb"))
                time.sleep(1)

    def on_new_data(self, data):
        self.s1.clear()
        brushes = [
            pg.mkBrush(255, 0, 0),
            pg.mkBrush(0, 255, 0),
            pg.mkBrush(0, 0, 255)]

        i = 0

        for cluster in data:
            for c in cluster:
                self.s1.addPoints(pos=c, brush=brushes[i % len(brushes)])
                i += 1

if __name__ == '__main__':
    import sys
    logging.basicConfig(filename='', level=logging.DEBUG)
    logging.getLogger("PyQt4").setLevel(logging.INFO)
    
    app = QtGui.QApplication(sys.argv)
    widget = LidarFrame(QtCore.QSettings("AlexLexx", "car_controlls"))
    widget.show()
    sys.exit(app.exec_())  