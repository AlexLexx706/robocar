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
        self.checkBox_record.setChecked(self.settings.value("lidar_record", True).toBool())

        ## create four areas to add plots
        self.w1 = self.view.addPlot()
        self.w1.showGrid(x=True, y=True)
        self.w1.setAspectLocked()
        
        self.s1 = pg.ScatterPlotItem(size=5, pen=pg.mkPen(None), brush=pg.mkBrush(255, 255, 255, 120))
        self.w1.addItem(self.s1)
        self.write_file = None
        

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
                self.new_data.emit(self.prepare_data(data))
                time.sleep(1)
                    
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
                self.new_data.emit(self.prepare_data(data))
                time.sleep(1.0)
            #конец файла
            except EOFError:
                stream = pickle.Unpickler(open(file_path, "rb"))
                time.sleep(1)

    def prepare_data(self, data):
        st = time.time()
        res = []
        for cluster in self.make_clusters(self.sector_to_data(data, start_angle=math.pi/2.0, max_len=1000)):
            if len(cluster) < 5:
                continue

            res.append(self.split_and_merge_cluster(cluster))
        print time.time() - st
        return res

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

    def sector_to_data(self, data, start_angle=0, max_len=1000):
        res = []
        da = data["angle"] / (len(data["values"]))
        data["values"].reverse()
        
        for i, value in enumerate(data["values"]):
            if max_len is not None and value > max_len:
                continue
                
            x = math.cos(start_angle + da * i) * value
            y = math.sin(start_angle + da * i) * value
            res.append((x, y, value))
        return res
    
    def make_clusters(self, points):
        '''кластиризуем последовательности точек после лидара'''
        if len(points) == 0:
            return []

        s_pos = points[0]
        clasters = [[s_pos, ]]

        def check(s_pos, c_pos):
            '''проверка группировки в кластер, по максимальному шагу'''
            l = (Vec2d(s_pos) - Vec2d(c_pos)).get_length()

            #найдём среднюю длинну
            max_offset = (min(s_pos[2], c_pos[2]) + abs(s_pos[2] - c_pos[2]) / 2.0) * math.pi / 180. * 6
            return l < max_offset
        
        #создадим кластеры 
        for c_pos in points[1:]:
            if check(s_pos, c_pos):
                clasters[-1].append(c_pos)
            else:
                clasters.append([c_pos,])
            s_pos = c_pos

        #обьединим перный и последний кластер
        if len(clasters) >= 2:
            if check(clasters[0][0], clasters[-1][-1]):
                clasters[-1].extend(clasters[0])
                clasters.pop(0)
        return clasters

    def split_and_merge_cluster(self, cluster):
        '''преобразуем кластер точек в набор прямых'''

        def split(cluster, res):
            '''Рекурсивное разделение кластера на маленькие линии'''
            threshold = 1

            #проверим максимальное отклонение от направления
            if len(cluster) > 2:
                #нормаль к прямой.
                s_pos = Vec2d(cluster[0])
                normal = (Vec2d(cluster[-1]) - s_pos).perpendicular_normal()

                #поиск максимума
                max = 0
                max_i = 0

                for i, pos in enumerate(cluster[1:-1]):
                    p = abs(normal.dot(Vec2d(pos) - s_pos))

                    if p > max:
                        max = p
                        max_i = i

                #делим кластер на два кластера
                if max > threshold:
                    split(cluster[:max_i + 2], res)
                    split(cluster[max_i + 1:], res)
                #не делим кластер
                else:
                    res.append(cluster)
            else:
                res.append(cluster)

        def merge(clusters):
            '''Обьединим соседние линии в одну если угол наклона не оч большой'''
            if len(clusters) > 1:
                threshold = 5

                first = clusters[0]
                i = 1
                no_merge = True

                while i < len(clusters):
                    cur = clusters[i]

                    #v = (Vec2d(first[-1]) - Vec2d(first[0])).normalized().get_angle_between((Vec2d(cur[-1]) - Vec2d(cur[0])).normalized())
                    v = (Vec2d(cur[-1]) - Vec2d(first[0])).perpendicular_normal().dot(Vec2d(first[-1]) - Vec2d(first[0]))

                    #проверка обьединения.
                    if abs(v) < threshold:
                        first.extend(cur)
                        clusters.pop(i)
                        no_merge = False
                    else:
                        i +=1
                        first = cur

                #мёржим пока всё не склеиться
                if not no_merge:
                    merge(clusters)


        #разделим на отдельные прямые
        res = []
        split(cluster, res)
        merge(res)
        return res


    
if __name__ == '__main__':
    import sys
    logging.basicConfig(filename='', level=logging.DEBUG)
    logging.getLogger("PyQt4").setLevel(logging.INFO)
    
    app = QtGui.QApplication(sys.argv)
    widget = LidarFrame(QtCore.QSettings("AlexLexx", "car_controlls"))
    widget.show()
    sys.exit(app.exec_())  