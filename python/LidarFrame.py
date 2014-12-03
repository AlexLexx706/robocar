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
from lidar.Vec2d import Vec2d
from lidar.LineFeaturesMaker import LineFeaturesMaker
from cross_detector.ffmpeg_reader import FFmpegReader
import Queue

logger = logging.getLogger(__name__)

class LidarFrame(QtGui.QFrame):
    new_data = pyqtSignal(object)
    new_video_frame = pyqtSignal("QImage")
    
    def __init__(self, settings, parent=None, in_gueue_sector_data = None):
        super(QtGui.QFrame, self).__init__(parent)
        uic.loadUi(os.path.join(os.path.split(__file__)[0], "LidarFrame.ui"), self)
        self.settings = settings
                
        self.view = pg.GraphicsLayoutWidget()  ## GraphicsView with GraphicsLayout inserted by default
        self.view_layout.addWidget(self.view)
        self.stop_flag = True
        self.new_data.connect(self.on_new_data)
        self.lineEdit_host.setText(self.settings.value("lidar_host", "192.168.0.91").toString())
        self.spinBox_port.setValue(self.settings.value("lidar_port", 8080).toInt()[0])
        
        self.groupBox_connection.setChecked(self.settings.value("lidar_use_connection", True).toBool())
        self.checkBox_record.setChecked(self.settings.value("lidar_record", False).toBool())
        self.groupBox_use_step.setChecked(self.settings.value("lidar_use_step", False).toBool())

        ## create four areas to add plots
        self.plot = self.view.addPlot()
        self.plot.showGrid(x=True, y=True)
        self.plot.setAspectLocked()

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
        
        if self.in_gueue_sector_data is not None:
            self.start()

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
        url = (unicode(self.lineEdit_host.text()), self.spinBox_port.value())

        if self.stop_flag:
            self.stop_flag = False
            self.first_draw = True
            self.frame_number = 0
            
            #чтение из очереди
            if self.in_gueue_sector_data is not None:
                self.read_thread = threading.Thread(target=self.read_queue_proc)
            else:
                out_file = unicode(self.settings.value("lidar_record_file", "data.dat").toString())

                #запуск чтения с датчика
                if self.groupBox_connection.isChecked():
                    self.read_thread = threading.Thread(target=self.read_server_proc, args=(url, out_file if self.checkBox_record.isChecked() else None))
                #запуск из файла
                else:
                    self.read_thread = threading.Thread(target=self.read_file_proc, args=(out_file, ))
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

    def read_server_proc(self, url, out_file):
        client = Client(url)
        
        #Создадим поток для записи данных
        if out_file is not None:
            out_file = pickle.Pickler(open(out_file, "wb"))

        self.lines_before = None
        self.odometry_angle = 0.0

        while not self.stop_flag:
            data = client.ik_get_sector(1)

            if data is not None:
                self.prepare_data(data[0])

                #пишем поток.
                if out_file is not None:
                    out_file.dump(data)

                self.wait_next_step()

    def read_file_proc(self, file_path):
        if not os.path.exists(file_path):
            return

        stream = pickle.Unpickler(open(file_path, "rb"))
        self.lines_before = None
        self.odometry_angle = 0.0


        while not self.stop_flag:
            try:
                data = stream.load()
                self.prepare_data(data)
                if not self.wait_next_step():
                    time.sleep(0.25)
            #конец файла
            except EOFError:
                stream = pickle.Unpickler(open(file_path, "rb"))
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

            draw_data = {"frame_number": self.frame_number,
                         "primetives": data}
            self.frame_number += 1

            print 'read_queue_proc'
            self.new_data.emit(draw_data)


    def prepare_data(self, data):
        points = self.lfm.sector_to_points(data)

        #1. Отобразим точки
        primetives = [{"points": points, "color":(255, 0, 0), "size": 2}, ]

        #2. найдём кластеры линий.
        if 0:
            clasters = self.lfm.sector_to_lines_clusters(points)

            i = 0
            for c_l in clasters:
                for c in c_l:
                    primetives.append({"line": self.lfm.point_to_line_sqr_approx(c), "color":(0, 255, 0), "text": str(i), "width":3})
                    i += 1

        draw_data = {"frame_number": self.frame_number,
                     "primetives": primetives}

        self.frame_number += 1
        self.new_data.emit(draw_data)

    def draw_points(self, info):
        '''
        Отображает точки, в формате:{
            "points": [Vec2d,...],
            "color":(r,g,b,a), - опционально
            "size": int - опционально
        }
        '''
        spi = pg.ScatterPlotItem()
        spi.setData(pos=info["points"])

        if "size" in info:
            spi.setSize(info["size"])

        if "color" in info:
            spi.setBrush(pg.mkBrush(info["color"]))

        self.plot.addItem(spi)

    def draw_line(self, info):
        '''
        Отображает точки, в формате:{
            "line":{"pos": Vec2d, "end": Vec2d}
            "color": (r,g,b,a) - опционально,
            "width":int - опционально, толщина линии
        }
        '''

        line = self.plot.plot([{"x": info["line"]["pos"][0], "y":info["line"]["pos"][1]},
                        {"x": info["line"]["end"][0], "y":info["line"]["end"][1]}])

        if "color" in info :
            if "width" in info:
                line.setPen(color=info["color"], width=info["width"])
            else:
                line.setPen(color=info["color"])

        #Вместе с текстом
        if "text" in info:
            if "color" in info["color"]:
                text = pg.TextItem(info["text"], color=info["color"])
            else:
                text = pg.TextItem(info["text"])

            text.setPos(info["line"]["pos"][0], info["line"]["pos"][1])
            self.plot.addItem(text)




    def draw_text(self, info):
        '''
        Отображает текст в формате:{
            "text":"",
            "pos":[x,y]
            "color": (r,g,b,a) - опционально
        }
        '''

        if "color" in info:
            text = pg.TextItem(info["text"], color=info["color"])
        else:
            text = pg.TextItem(info["text"])

        text.setPos(info["pos"][0], info["pos"][1])
        self.plot.addItem(text)

    def on_new_data(self, data):
        self.plot.clear()
        self.label_frame.setText(str(data["frame_number"]))

        #рисуем новые данные
        for p in data["primetives"]:
            if "points" in p:
                self.draw_points(p)
            elif "line" in p:
                self.draw_line(p)
            elif "text" in p:
                self.draw_text(p)

        if self.first_draw:
            self.plot.autoRange()
            self.first_draw = False



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
