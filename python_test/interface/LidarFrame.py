# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import pyqtSlot, pyqtSignal
import pyqtgraph as pg
import numpy as np
import logging
import threading
logger = logging.getLogger(__name__)
from aproximation_tools import sector_to_data
import math
from tcp_rpc.client import Client


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

        ## create four areas to add plots
        self.w1 = self.view.addPlot()
        self.w1.showGrid(x=True, y=True)
        
        self.s1 = pg.ScatterPlotItem(size=5, pen=pg.mkPen(None), brush=pg.mkBrush(255, 255, 255, 120))
        self.w1.addItem(self.s1)

    def closeEvent(self, event):
        self.stop()
        QtGui.QFrame.closeEvent(self, event)
        
    
    @pyqtSlot()
    def on_lineEdit_host_editingFinished(self):
        self.settings.setValue("lidar_host", self.lineEdit_host.text())
    
    @pyqtSlot(int)
    def on_spinBox_port_valueChanged(self, value):
        print value
        self.settings.setValue("lidar_port", self.spinBox_port.value())
    
    @pyqtSlot(bool)
    def on_pushButton_connect_clicked(self, v):
        if self.stop_flag:
            self.pushButton_connect.setText(u"Отключить")
            self.start()
        else:
            self.pushButton_connect.setText(u"Подключить")
            self.stop()

    def start(self):
        url = (unicode(self.lineEdit_host.text()), self.spinBox_port.value())

        if self.stop_flag:
            self.stop_flag = False
            self.read_thread = threading.Thread(target=self.read_proc, args=(url, ))
            self.read_thread.start()
    
    def stop(self):
        if not self.stop_flag:
            self.stop_flag = True
            self.read_thread.join()

    def read_proc(self, url):
        client = Client(url)

        while not self.stop_flag:
            data = client.ik_get_sector(1)
            if data is not None:
                self.new_data.emit(data[0])
    
    def on_new_data(self, data):
        points = self.sector_to_data(data, start_angle=math.pi/2.0)
        self.s1.setData(pos=points)
        #self.s1.setData(pos=[[10,5],])

    def sector_to_data(self, data, start_angle=0):
        res = []
        da = data["angle"] / (len(data["values"]))
        data["values"].reverse()
        
        for i, value in enumerate(data["values"]):
            x = math.cos(start_angle + da * i) * value
            y = math.sin(start_angle + da * i) * value
            res.append((x, y))
        return res
        
if __name__ == '__main__':
    import sys
    logging.basicConfig(filename='', level=logging.DEBUG)
    logging.getLogger("PyQt4").setLevel(logging.INFO)
    
    app = QtGui.QApplication(sys.argv)
    widget = LidarFrame(QtCore.QSettings("AlexLexx", "car_controlls"))
    widget.show()
    sys.exit(app.exec_())  