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
from lidar.Vec2d import Vec2d
from lidar.LineFeaturesMaker import LineFeaturesMaker
from cross_detector.ffmpeg_reader import FFmpegReader
from data_view_2 import DataView
#from data_view import DataView
import Queue
import right_wall_lidar_motion


logger = logging.getLogger(__name__)

class LidarFrame(QtGui.QFrame):
    new_data = pyqtSignal(object)
    new_video_frame = pyqtSignal("QImage")
    close_window = pyqtSignal()
    
    def __init__(self, settings, parent=None, in_gueue_sector_data = None):
        super(QtGui.QFrame, self).__init__(parent)
        uic.loadUi(os.path.join(os.path.split(__file__)[0], "LidarFrame.ui"), self)
        self.settings = settings
                
        self.view = DataView()
        self.view_layout.addWidget(self.view)
        self.stop_flag = True
        self.new_data.connect(self.on_new_data)
        self.close_window.connect(self.close)
        self.lineEdit_host.setText(self.settings.value("lidar_host", "192.168.0.91").toString())
        self.spinBox_port.setValue(self.settings.value("lidar_port", 8080).toInt()[0])
        
        self.groupBox_connection.setChecked(self.settings.value("lidar_use_connection", True).toBool())
        self.checkBox_record.setChecked(self.settings.value("lidar_record", False).toBool())
        self.groupBox_use_step.setChecked(self.settings.value("lidar_use_step", False).toBool())
        
        self.write_file = None
        self.lfm = LineFeaturesMaker()
        
        self.video_thread = None
        self.new_video_frame.connect(self.on_new_video_frame)
        self.lines_before = None
        self.odometry_angle = 0.0
        self.data_before =  None
        self.next_event = threading.Event()
        self.in_gueue_sector_data = in_gueue_sector_data
        self.first_draw = True
        self.label_frame.setText("0")
        self.frame_number = 0
        
        self.init_sector_controlls()
        self.init_alg_controlls()
        
        self.update_control_angle = None
        
        if self.in_gueue_sector_data is not None:
            self.start()
            self.groupBox_connection.setEnabled(False)
         
            
    def on_new_data(self, data):
        self.label_frame.setText(str(data["frame_number"]))
        self.view.draw_data(data)

    @pyqtSlot(bool)
    def on_groupBox_use_step_clicked(self, checked):
        if not checked:
            self.next_event.set()

        self.settings.setValue("lidar_use_step", checked)

    def start_video(self):
        if self.video_thread is None:
            self.reader = FFmpegReader()
            self.video_thread = threading.Thread(target=self.read_frame)
            self.video_thread.start()
    
    def stop_video(self):
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
            self.stop_video()
            self.pushButton_start_video.setText(u"Запустить видео")
        else:
            self.start_video()
            self.pushButton_start_video.setText(u"Остановить видео")

        
        
    def on_new_video_frame(self, image):
        self.label_video.setPixmap(QtGui.QPixmap.fromImage(image))

    def closeEvent(self, event):
        self.stop()
        self.stop_video()
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
            self.start()
        else:
            self.stop()

    @pyqtSlot(bool)
    def on_groupBox_connection_clicked(self, v):
        self.settings.setValue("lidar_use_connection", v)
        
    @pyqtSlot(bool)
    def on_checkBox_record_toggled(self, v):
        self.settings.setValue("lidar_record", v)

    @pyqtSlot(bool)
    def on_pushButton_next_clicked(self):
        self.next_event.set()

    def start(self):
        if self.stop_flag:
            self.stop_flag = False
            self.first_draw = True
            self.frame_number = 0
            self.data_file = unicode(self.settings.value("lidar_record_file", "data.dat").toString())
            self.url = (unicode(self.lineEdit_host.text()), self.spinBox_port.value())

            #чтение из очереди
            if self.in_gueue_sector_data is not None:
                if not self.checkBox_record.isChecked():
                    self.data_file = None
                self.read_thread = threading.Thread(target=self.read_queue_proc)
            else:
                #запуск чтения с датчика
                if self.groupBox_connection.isChecked():
                    if not self.checkBox_record.isChecked():
                        self.data_file = None
                    self.read_thread = threading.Thread(target=self.read_server_proc)
                #запуск из файла
                else:
                    self.read_thread = threading.Thread(target=self.read_file_proc)
            self.pushButton_control.setText(u"Стоп")
            self.read_thread.start()
    
    def stop(self):
        if not self.stop_flag:
            self.stop_flag = True
            self.next_event.set()
            self.read_thread.join()
            self.pushButton_control.setText(u"Старт")

    def calcl_odometry(self, lines):
        return
        #найдём похожие линии.
        if self.lines_before is not None:
            similar = self.lfm.search_similar(self.lines_before, lines)
            print similar
            #self.odometry_angle += similar
            #print self.odometry_angle

        self.lines_before = lines

    def wait_next_step(self):
        if self.groupBox_use_step.isChecked():
            self.next_event.wait()
            self.next_event.clear()
            return True
        return False

    def read_server_proc(self):
        client = Client(self.url, serialization="mesgpack")
        
        #Создадим поток для записи данных
        if self.data_file is not None:
            self.data_file = pickle.Pickler(open(self.data_file, "wb"))

        while not self.stop_flag:
            data = client.ik_get_sector(1)

            if data is not None:
                data = data[0]
                self.prepare_data(data)

                #пишем поток.
                if self.data_file is not None:
                    self.data_file.dump(data)

                self.wait_next_step()

    def read_file_proc(self):
        if not os.path.exists(self.data_file):
            return

        stream = pickle.Unpickler(open(self.data_file, "rb"))

        while not self.stop_flag:
            try:
                data = stream.load()
                self.prepare_data(data)
                if not self.wait_next_step():
                    time.sleep(0.1)
            #конец файла
            except EOFError:
                stream = pickle.Unpickler(open(self.data_file, "rb"))
                time.sleep(1)

    def read_queue_proc(self):
        if self.data_file is not None:
            self.data_file = pickle.Pickler(open(self.data_file, "wb"))

        while not self.stop_flag:
            try:
                self.wait_next_step()
                data = self.in_gueue_sector_data.get(timeout=1)
            except Queue.Empty:
                continue

            if data is None:
                self.close_window.emit()
                return

            draw_data = {"frame_number": self.frame_number, "primetives": []}

            if "primetives" in data:
                draw_data["primetives"].extend(data["primetives"])

            if "sector" in data:
                draw_data["primetives"].extend(self.sector_2_primetives(data["sector"]))

                #Запись данных
                if self.data_file is not None:
                    self.data_file.dump(data["sector"])

            self.frame_number += 1
            self.new_data.emit(draw_data)


    def sector_2_primetives(self, data):
        primetives = self.draw_clusters(data)
        primetives.extend(self.draw_alg(data))
        return primetives
        
    
    def draw_clusters(self, data):
        primetives = []
        
        if self.groupBox_show_sector.isChecked():
            points = self.lfm.sector_to_points(data,
                                                start_angle=self.doubleSpinBox_start_angle.value(),
                                                max_radius=self.doubleSpinBox_max_radius.value())
            if self.groupBox_show_points.isChecked():
                primetives.append({"points": points, "color":(255, 0, 0), "size": self.spinBox_points_size.value()})

            #2. найдём кластеры линий.
            if self.groupBox_show_clusters.isChecked():
                #Кластеры точек
                if self.checkBox_show_points_clusters.isChecked():
                    clasters = self.lfm.sector_to_points_clusters(points,
                                                max_offset = self.doubleSpinBox_max_offset.value(),
                                                min_cluster_len=self.spinBox_min_cluster_len.value(),
                                                start_angle=self.doubleSpinBox_start_angle.value(),
                                                max_radius=self.doubleSpinBox_max_radius.value())
                    for i, c in enumerate(clasters):
                        color = QtGui.QColor(QtCore.Qt.GlobalColor(3+i%19)).getRgb()[:-1]
                        primetives.append({"points": c, "color": color, "size": self.spinBox_clasters_size.value()})

                if self.groupBox_show_lines_clusters.isChecked():
                    clasters = self.lfm.sector_to_lines_clusters(points,
                                                max_offset = self.doubleSpinBox_max_offset.value(),
                                                min_cluster_len=self.spinBox_min_cluster_len.value(),
                                                split_threshold=self.doubleSpinBox_split_threshold.value(),
                                                merge_threshold=math.cos(self.doubleSpinBox_merge_threshold.value()/180.*math.pi))

                    if self.checkBox_show_line_cluster_points.isChecked():
                        for i, c in enumerate(clasters):
                            color = QtGui.QColor(QtCore.Qt.GlobalColor(3+i%19)).getRgb()[:-1]
                            primetives.append({"points": c, "color": color, "size": self.spinBox_clasters_size.value()})
                    
                    if self.checkBox_show_line_cluster_lines.isChecked():
                        for i, c in enumerate(clasters):
                            color = QtGui.QColor(QtCore.Qt.GlobalColor(3+i%19)).getRgb()[:-1]
                            primetives.append({"line": {"pos":c[0], "end": c[-1]}, "color": color})
        return primetives
    
    def draw_alg(self, data):
        if self.groupBox_show_alg.isChecked() and data is not None:
            right_wall_lidar_motion.DELTA = self.doubleSpinBox_alg_DELTA.value()
            right_wall_lidar_motion.WALL_ANALYSIS_DX_GAP = self.doubleSpinBox_alg_WALL_ANALYSIS_DX_GAP.value()
            right_wall_lidar_motion.WALL_ANALYSIS_ANGLE = int(self.doubleSpinBox_alg_WALL_ANALYSIS_ANGLE.value())
            right_wall_lidar_motion.MIN_LIDAR_DISTANCE = self.doubleSpinBox_alg_MIN_LIDAR_DISTANCE.value()
            right_wall_lidar_motion.MAX_LIDAR_DISTANCE = self.doubleSpinBox_alg_MAX_LIDAR_DISTANCE.value()
            right_wall_lidar_motion.TRUSTABLE_LIDAR_DISTANCE = self.doubleSpinBox_alg_TRUSTABLE_LIDAR_DISTANCE.value()

            right_wall_lidar_motion.MIN_GAP_WIDTH = self.doubleSpinBox_alg_MIN_GAP_WIDTH.value()

            right_wall_lidar_motion.Dr = self.doubleSpinBox_alg_Dr.value()
            right_wall_lidar_motion.Da = self.doubleSpinBox_alg_Da.value()
            right_wall_lidar_motion.Dh = self.doubleSpinBox_alg_Dh.value()
            
            move_res = right_wall_lidar_motion.move(data)
            
            if move_res is not None and 'primitives' in move_res:
                dir_dist = 100
                dir_line = {"line": {'pos':(0,0),
                                     'end': (dir_dist * math.cos(math.pi / 2.0 + move_res['turn_angle']),
                                             dir_dist * math.sin(math.pi / 2.0 + move_res['turn_angle']))},
                           "color":(0, 255, 0)}
                move_res["primitives"].append(dir_line)
                
                #Добавим в алгоритм управления данные
                if self.update_control_angle is not None:
                    self.update_control_angle(move_res['turn_angle'])
                
                return move_res["primitives"]

        return []
                
                
    @pyqtSlot(bool)
    def prepare_data(self, data):
        draw_data = {"frame_number": self.frame_number, "primetives": self.sector_2_primetives(data)}
        self.frame_number += 1
        self.new_data.emit(draw_data)
    
    
    ###########################################################################
    @pyqtSlot(bool)
    def on_groupBox_show_sector_toggled(self, state):
        self.settings.setValue("lidar_show_sector", state)
        
    @pyqtSlot("double")
    def on_doubleSpinBox_start_angle_valueChanged(self, value):
        self.settings.setValue("lidar_start_angle", value)
        
    @pyqtSlot("double")
    def on_doubleSpinBox_max_radius_valueChanged(self, value):
        self.settings.setValue("lidar_max_radius", value)

    @pyqtSlot("int")
    def on_spinBox_points_size_valueChanged(self, value):
        self.settings.setValue("lidar_points_size", value)
        
    @pyqtSlot("bool")
    def on_groupBox_show_points_toggled(self, value):
        self.settings.setValue("lidar_points", value)
       
    @pyqtSlot(bool)
    def on_groupBox_show_clusters_toggled(self, state):
        self.settings.setValue("lidar_show_clusters", state)

    @pyqtSlot("int")
    def on_spinBox_clasters_size_valueChanged(self, value):
        self.settings.setValue("lidar_clasters_size", value)
    
    @pyqtSlot("double")
    def on_doubleSpinBox_max_offset_valueChanged(self, value):
        self.settings.setValue("lidar_max_offset", value)

    @pyqtSlot("int")
    def on_spinBox_min_cluster_len_valueChanged(self, value):
        self.settings.setValue("lidar_min_cluster_len", value)
    
    @pyqtSlot(bool)
    def on_checkBox_show_points_clusters_toggled(self, state):
        self.settings.setValue("lidar_show_points_clusters", state)
   
    @pyqtSlot(bool)
    def on_groupBox_show_lines_clusters_toggled(self, state):
        self.settings.setValue("lidar_show_lines_clusters", state)
    
    @pyqtSlot("double")
    def on_doubleSpinBox_split_threshold_valueChanged(self, value):
        self.settings.setValue("lidar_split_threshold", value)

    @pyqtSlot("double")
    def on_doubleSpinBox_merge_threshold_valueChanged(self, value):
        self.settings.setValue("lidar_merge_threshold", value)
    
    @pyqtSlot(bool)
    def on_checkBox_show_line_cluster_points_toggled(self, state):
        self.settings.setValue("lidar_show_line_cluster_points", state)
    
    def on_checkBox_show_line_cluster_lines_toggled(self, state):
        self.settings.setValue("lidar_show_line_cluster_lines", state)
    
    
    def init_sector_controlls(self):
        self.groupBox_show_sector.setChecked(self.settings.value("lidar_show_sector", True).toBool())
        self.doubleSpinBox_start_angle.setValue(self.settings.value("lidar_start_angle", 1.57).toDouble()[0])
        self.doubleSpinBox_max_radius.setValue(self.settings.value("lidar_max_radius", 1000).toInt()[0])
        self.groupBox_show_points.setChecked(self.settings.value("lidar_points", True).toBool())
        self.groupBox_show_clusters.setChecked(self.settings.value("lidar_show_clusters", True).toBool())
        self.spinBox_clasters_size.setValue(self.settings.value("lidar_clasters_size", 3).toInt()[0])
        self.doubleSpinBox_max_offset.setValue(self.settings.value("lidar_max_offset", 30.0).toDouble()[0])
        self.spinBox_min_cluster_len.setValue(self.settings.value("lidar_min_cluster_len", 0).toInt()[0])
        self.checkBox_show_points_clusters.setChecked(self.settings.value("lidar_show_points_clusters", True).toBool())
        self.groupBox_show_lines_clusters.setChecked(self.settings.value("lidar_show_lines_clusters", True).toBool())
        self.doubleSpinBox_split_threshold.setValue(self.settings.value("lidar_split_threshold", 2.0).toDouble()[0])
        self.doubleSpinBox_merge_threshold.setValue(self.settings.value("lidar_merge_threshold", 10).toDouble()[0])
        self.checkBox_show_line_cluster_points.setChecked(self.settings.value("lidar_show_line_cluster_points", True).toBool()) 
        self.checkBox_show_line_cluster_lines.setChecked(self.settings.value("lidar_show_line_cluster_lines", True).toBool())

    #######################################################
    @pyqtSlot("double")
    def on_doubleSpinBox_alg_DELTA_valueChanged(self, value):
        self.settings.setValue("lidar_alg_DELTA", value)

    @pyqtSlot("double")
    def on_doubleSpinBox_alg_WALL_ANALYSIS_DX_GAP_valueChanged(self, value):
        self.settings.setValue("lidar_alg_WALL_ANALYSIS_DX_GAP", value)

    @pyqtSlot("double")
    def on_doubleSpinBox_alg_WALL_ANALYSIS_ANGLE_valueChanged(self, value):
        self.settings.setValue("lidar_alg_WALL_ANALYSIS_ANGLE", value)        

    @pyqtSlot("double")
    def on_doubleSpinBox_alg_MIN_LIDAR_DISTANCE_valueChanged(self, value):
        self.settings.setValue("lidar_alg_MIN_LIDAR_DISTANCE", value) 

    @pyqtSlot("double")
    def on_doubleSpinBox_alg_MAX_LIDAR_DISTANCE_valueChanged(self, value):
        self.settings.setValue("lidar_alg_MAX_LIDAR_DISTANCE", value) 
   
    @pyqtSlot("double")
    def on_doubleSpinBox_alg_TRUSTABLE_LIDAR_DISTANCE_valueChanged(self, value):
        self.settings.setValue("lidar_alg_TRUSTABLE_LIDAR_DISTANCE", value) 

    @pyqtSlot("double")
    def on_doubleSpinBox_alg_MIN_GAP_WIDTH_valueChanged(self, value):
        self.settings.setValue("lidar_alg_MIN_GAP_WIDTH", value) 

    @pyqtSlot("double")
    def on_doubleSpinBox_alg_Dr_valueChanged(self, value):
        self.settings.setValue("lidar_alg_Dr", value) 

    @pyqtSlot("double")
    def on_doubleSpinBox_alg_Da_valueChanged(self, value):
        self.settings.setValue("lidar_alg_Da", value)
        
    @pyqtSlot("double")
    def on_doubleSpinBox_alg_Dh_valueChanged(self, value):
        self.settings.setValue("lidar_alg_Dh", value)        

    def init_alg_controlls(self):
        self.doubleSpinBox_alg_DELTA.setValue(self.settings.value("lidar_alg_DELTA", 70.0).toDouble()[0])
        self.doubleSpinBox_alg_WALL_ANALYSIS_DX_GAP.setValue(self.settings.value("lidar_alg_WALL_ANALYSIS_DX_GAP", 15).toDouble()[0])
        self.doubleSpinBox_alg_WALL_ANALYSIS_ANGLE.setValue(self.settings.value("lidar_alg_WALL_ANALYSIS_ANGLE", 90).toDouble()[0])
        self.doubleSpinBox_alg_MIN_LIDAR_DISTANCE.setValue(self.settings.value("lidar_alg_MIN_LIDAR_DISTANCE", 20).toDouble()[0])
        self.doubleSpinBox_alg_MAX_LIDAR_DISTANCE.setValue(self.settings.value("lidar_alg_MAX_LIDAR_DISTANCE", 600).toDouble()[0])
        self.doubleSpinBox_alg_TRUSTABLE_LIDAR_DISTANCE.setValue(self.settings.value("lidar_alg_TRUSTABLE_LIDAR_DISTANCE", 400).toDouble()[0])
        self.doubleSpinBox_alg_MIN_GAP_WIDTH.setValue(self.settings.value("lidar_alg_MIN_GAP_WIDTH", 50).toDouble()[0])
        self.doubleSpinBox_alg_Dr.setValue(self.settings.value("lidar_alg_Dr", 30).toDouble()[0])
        self.doubleSpinBox_alg_Da.setValue(self.settings.value("lidar_alg_Da", 0.1).toDouble()[0])
        self.doubleSpinBox_alg_Dh.setValue(self.settings.value("lidar_alg_Dh", 0.70).toDouble()[0])

        
def data_from_server(in_queue):
    client = Client(("192.168.10.154", 8080))

    while 1:
        data = client.ik_get_sector(1)
        in_queue.put(data[0])
        
def main(in_queue):
    import sys
    app = QtGui.QApplication(sys.argv)
    widget = LidarFrame(QtCore.QSettings("AlexLexx", "car_controlls"), in_gueue_sector_data=in_queue)
    widget.show()
    sys.exit(app.exec_())
        

if __name__ == '__main__':
    logging.basicConfig(filename='', level=logging.DEBUG)
    logging.getLogger("PyQt4").setLevel(logging.INFO)

    in_queue = Queue.Queue()
    in_queue = None
    #threading.Thread(target=data_from_server, args=(in_queue,)).start()
    main(in_queue)

    #main(None)
