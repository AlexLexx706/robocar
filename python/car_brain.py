# -*- coding: utf-8 -*-
from car_controll.protocol import Protocol
import time
import math
from Queue import Queue
from threading import Thread
from threading import Lock
from tcp_rpc.client import Client
from lidar.LineFeaturesMaker import LineFeaturesMaker
import logging
import os
import pickle
from lidar.Vec2d import Vec2d

logger = logging.getLogger(__name__)

class CarBrain(Thread):
    MIN_HOLE_LEN = 60
    ROBOT_RADIUS = 20
    MAX_LIDAR_RADIUS = 350
    MIN_CLUSTER_LEN = 5

    class LidarDataProvider:
        '''Читает данные из лидара или из файла'''
        def __init__(self, url):
            self.url = url
            self.stream = None

            if not isinstance(self.url, basestring):
                self.client = Client(self.url)
            else:
                if not os.path.exists(self.url):
                    raise RuntimeError("file:{} not exist".format(self.url))
                self.stream = pickle.Unpickler(open(self.url, "rb"))
                self.st = time.time()
                self.delay = 1.0 / 4.0

        def next(self):
            if self.stream is not None:
                try:
                    dt = time.time() - self.st

                    if dt <= self.delay:
                        time.sleep(self.delay - dt)

                    try:
                        return self.stream.load()
                    except EOFError:
                        self.stream = pickle.Unpickler(open(self.url, "rb"))
                        return self.stream.load()
                finally:
                    self.st = time.time()
            return self.client.ik_get_sector(1)[0]



    def __init__(self, protocol_url=(1, {"host":"192.168.0.91", "port":1111}),
                 lidar_url=("192.168.0.91", 8080),
                 use_gui=True,
                 use_control=True):
        try:
            logger.debug("->")
            Thread.__init__(self)

            self.res_queue = Queue()
            self.protocol = Protocol(self.res_queue)
            self.lfm = LineFeaturesMaker()
            self.protocol_url = protocol_url
            self.lidar_url = lidar_url
            self.use_gui = use_gui
            self.use_control = use_control

            #поток чтения сообщений из машины
            self.rpm_thread = Thread(target=self.rpm_proc)
            
            #поток обработки данных лидара
            self.lidar_thread = Thread(target=self.lidar_proc)
            self.hole_lock = Lock()
            self.hole = None
            self.stop_flag = False
        finally:
            logger.debug("<-")

    def get_hole(self):
        with self.hole_lock:
            return self.hole
    
    def start(self):
        try:
            logger.debug("->")

            #потоки управления
            if self.use_control:
                if not self.protocol.connect(*self.protocol_url):
                    logger.error("Cannot connect to: {}".format(self.protocol_url))
                    return

                Thread.start(self)
                self.rpm_thread.start()

            #отображалка
            if self.use_gui:
                import multiprocessing
                from LidarFrame import main
                self.data_queue_for_gui = multiprocessing.Queue(1)
                multiprocessing.Process(target=main, args=(self.data_queue_for_gui,)).start()

            self.lidar_thread.start()
        finally:
            logger.debug("<-")
    
    def stop(self):
        try:
            logger.debug("->")

            self.stop_flag = True

            if self.use_control:
                self.res_queue.put(None)
                self.join()
                self.rpm_thread.join()
                self.protocol.set_power_zerro()
                self.protocol.close()

            self.lidar_thread.join()
        finally:
            logger.debug("<-")
        

    def run(self):
        try:
            logger.debug("->")
            #поток управления машиной.
            angle_speed = math.pi * 0.5
            time.sleep(3)
            self.protocol.set_pid_settings(0, 2, 0.2, 0.1)
            self.protocol.set_info_period(1000000)
            asinch = True
            self.protocol.set_offset(0.5)

            while not self.stop_flag:
                hole = self.get_hole()

                if hole is not None:
                    angle = -(90. - hole["direction"].get_angle()) / 180. * math.pi
                    self.protocol.turn(angle, angle_speed, asinch)
                else:
                    self.protocol.turn(math.pi * 0.5, angle_speed, asinch)
                time.sleep(0.25)
        finally:
            logger.debug("<-")

    def rpm_proc(self):
        try:
            logger.debug("->")

            while not self.stop_flag:

                #если усё повисло
                data = self.res_queue.get()

                if data is None:
                    return

                if data[0] == 0:
                    logger.info(data[1])
                elif data[0] == 1:
                    logger.info("giro:{:10.4f}".format(data[1][0]))
        finally:
            logger.debug("<-")

    def check_intersection(self, direction, line):
        normal = direction.normalized()

        #1. проверка проекции на направление
        proj_p1 = normal.dot(line["pos"])
        proj_p2 = normal.dot(line["end"])
        proj_half = (proj_p2 - proj_p1) / 2.0
        dir_half = direction.get_length() / 2.0

        #нет пересечения
        if abs((proj_p1 + proj_half) - dir_half) > (dir_half + abs(proj_half)):
            return None

        #2. проверка проекции на перпендикуляр
        proj = normal.perpendicular()

        #спроецируем линию на перпендикуляр
        proj_p1 = proj.dot(line["pos"])
        proj_p2 = proj.dot(line["end"])

        #проверка пересечения направления с линией
        proj_half = (proj_p2 - proj_p1) / 2.0

        #есть пересечение с направления с линией.
        if abs(proj_p1 + proj_half) > (self.ROBOT_RADIUS + abs(proj_half)):
            return None

        if abs(proj_p1) < abs(proj_p2):
            return line["pos"]

        return line["end"]

    def lidar_proc(self ):
        try:
            logger.debug("->")

            provider = self.LidarDataProvider(self.lidar_url)

            while not self.stop_flag:
                data = provider.next()
                
                if data is None:
                    continue

                #1. найдём кластеры точек
                #points = self.lfm.sector_to_points(data, start_angle=math.pi/2.0, )
                clusters = self.lfm.sector_to_points_clusters(data,
                                                              max_radius=self.MAX_LIDAR_RADIUS,
                                                              min_cluster_len=self.MIN_CLUSTER_LEN)
                lines = self.lfm.clusters_to_lines(clusters)
                #lines = self.lfm.clusters_to_lines(self.lfm.sector_to_lines_clusters(points))

                #2. анализ расстояния между кластерами
                if len(lines) > 1:
                    holes = []

                    for i in range(len(lines)):
                        hole = self.lfm.pair_points_to_line(lines[i - 1]["end"], lines[i]["pos"])

                        #Проверка длинны прохода
                        if hole["length"]  < self.MIN_HOLE_LEN:
                            continue

                        hole["angle"] = hole["center"].get_angle()

                        #проверка сектора обзора
                        if hole["angle"] < 0.0:
                            continue

                        #выбор направление движения с учётом обьезда препятствия

                        holes.append(hole)

                    #сортируем проходы по нормали
                    holes = sorted(holes, key=lambda s : s["angle"])

                    intersected = []

                    #уточним направление движения
                    if len(holes):
                        hole = holes[0]
                        hole["direction"] = hole["center"]

                        #уточним направление движения.

                        for line in lines:
                            pos = self.check_intersection(hole["direction"], line)

                            if pos is not None:
                                intersected.append({"line": line, "color": (0, 0, 255)})
                                hole["direction"] += line["normal"] * self.ROBOT_RADIUS

                        if self.use_gui:
                            intersected.append({"line": {"pos": Vec2d(0, 0), "end": hole["direction"]}, "color":(255, 255, 255)})

                    with self.hole_lock:
                        self.hole = holes[0] if len(holes) else None
                        
                    #Отправим в отображалку
                    if self.use_gui:
                        from PyQt4 import QtGui, QtCore

                        primitives = [{"points": c, "color": QtGui.QColor(QtCore.Qt.GlobalColor(3 + i % 19)).getRgb()[:-1],
                                        "size": 3} for i, c in enumerate(clusters)]
                        primitives.extend(intersected)

                        if len(holes):
                            primitives.append({"line": holes[0], "color":(255, 0, 0)})

                        #self.data_queue_for_gui.put({"primetives": primitives, "sector": data})
                        self.data_queue_for_gui.put({"primetives": primitives})
        finally:
            self.data_queue_for_gui.put(None)
            logger.debug("<-")


if __name__ == "__main__":
    #logging.getLogger("protocol").setLevel(50)
    logging.basicConfig(format='%(levelname)s %(name)s::%(funcName)s %(message)s', level=logging.DEBUG)

    protocol_url = (1, {"host": "192.168.10.154", "port": 1111})
    #protocol_url = (1, {"host": "192.168.0.91", "port": 1111})
    #protocol_url = (0, {"port": "com26", "baudrate":115200, "timeout":2, "writeTimeout":2})
    #protocol_url = (0, {"port": "/dev/ttyUSB0", "baudrate":115200, "timeout":2, "writeTimeout":2})
    lidar_url = ("192.168.10.154", 8080)
    #lidar_url = "data.dat"
    #lidar_url = ("localhost", 8080)
    #lidar_url = ("192.168.0.91", 8080)

    cb = CarBrain(protocol_url, lidar_url, use_control=True)
    cb.start()
    try:
        while 1:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    cb.stop()