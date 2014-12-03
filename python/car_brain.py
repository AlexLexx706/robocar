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


USE_GUI = True
#USE_GUI = False

logger = logging.getLogger(__name__)

class CarBrain(Thread):
    def __init__(self, protocol_url=(1, {"host":"192.168.0.91", "port":1111}), lidar_url=("192.168.0.91", 8080)):
        try:
            logger.debug("->")
            Thread.__init__(self)

            self.res_queue = Queue()
            self.protocol = Protocol(self.res_queue)
            self.lfm = LineFeaturesMaker()
            self.protocol_url = protocol_url
            self.lidar_url = lidar_url

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
            if self.protocol.connect(*self.protocol_url):
                print "Connected to: {}".format(self.protocol_url)

                #отображалка
                if USE_GUI:
                    import multiprocessing
                    from LidarFrame import main
                    self.data_queue_for_gui = multiprocessing.Queue()
                    multiprocessing.Process(target=main, args=(self.data_queue_for_gui,)).start()

                self.rpm_thread.start()
                self.lidar_thread.start()
                Thread.start(self)
        finally:
            logger.debug("<-")
    
    def stop(self):
        try:
            logger.debug("->")

            self.stop_flag = True
            self.res_queue.put(None)
            self.join()
            self.rpm_thread.join()
            self.lidar_thread.join()
            self.protocol.set_power_zerro()
            self.protocol.close()
        finally:
            logger.debug("<-")
        

    def run(self):
        try:
            logger.debug("->")
            
            #while not self.stop_flag:
            #    time.sleep(1)
            #return

            #поток управления машиной.
            angle_speed = math.pi * 0.4
            time.sleep(5)
            self.protocol.set_pid_settings(0, 2, 0.2, 0.1)
            self.protocol.set_offset(0.35)

            while not self.stop_flag:
                hole = self.get_hole()
                if hole is not None:
                    angle = -(90. - hole["angle"]) /180. * math.pi
                    logger.debug("Turn angle:{}".format(angle))
                    self.protocol.turn(angle, angle_speed, True)
                else:
                    logger.debug("Turn 90!!!")
                    self.protocol.turn(math.pi / 2.0, angle_speed, True)
                
                time.sleep(0.25)
        finally:
            logger.debug("<-")

    def rpm_proc(self):
        try:
            logger.debug("->")

            while not self.stop_flag:
                data = self.res_queue.get()
                
                if data is None:
                    return 

                if data[0] == 0:
                    logger.debug(data[1])
        finally:
            logger.debug("<-")

    def lidar_proc(self ):
        try:
            logger.debug("->")

            client = Client(self.lidar_url)

            while not self.stop_flag:
                data = client.ik_get_sector(1)
                
                if data is None:
                    continue
                
                data = data[0]

                #1. найдём кластеры точек
                points = self.lfm.sector_to_points(data, start_angle=math.pi/2.0, max_len=300)
                lines = self.lfm.clusters_to_lines(self.lfm.sector_to_lines_clusters(points))

                #2. анализ расстояния между кластерами
                if len(lines) > 1:
                    holes = []
                    min_hole = 50

                    for i in range(len(lines)):
                        pos = lines[i - 1]["end"]
                        end = lines[i]["pos"]
                        direction = end - pos
                        center = pos + direction / 2.0
                        length = direction.normalize_return_length()
                        angle = center.get_angle()

                        #проверим проекцию длинну прохода
                        if length > min_hole and angle > 0.0:
                            n_angle = center.normalized().get_angle_between(direction)

                            if  n_angle > 30 and n_angle < 180-30:
                                normal = direction.perpendicular()
                                distance = center.get_length()

                                hole = {"pos": pos,
                                         "end": end,
                                         "dir": direction,
                                         "normal": normal,
                                         "length": length,
                                         "center": center,
                                         "distance": distance,
                                         "angle": center.get_angle(),
                                         "clasters":[i - 1, i]}

                                holes.append(hole)

                    #сортируем проходы по нормали
                    holes = sorted(holes, key=lambda s : s["angle"])

                    with self.hole_lock:
                        self.hole = holes[0] if len(holes) else None
                        
                        #if self.hole is not None:
                        #    print "angle:", self.hole["center"].normalized().get_angle_between(self.hole["dir"])

                    #Отправим в отображалку
                    if USE_GUI:
                        primitives = [{"line": l, "color": (0, 255, 0), "text": str(i)} for i, l in enumerate(lines)]
                        primitives.append({"points": points, "color": (0, 255, 0), "size": 3})

                        if len(holes):
                            primitives.append({"line": holes[0], "color":(255, 0, 0)})

                        self.data_queue_for_gui.put(primitives)
        finally:
            logger.debug("<-")


if __name__ == "__main__":
    #logging.getLogger("protocol").setLevel(50)
    logging.basicConfig(format='%(levelname)s %(name)s::%(funcName)s %(message)s', level=logging.DEBUG)

    #protocol_url = (1, {"host": "192.168.10.154", "port": 1111})
    protocol_url = (1, {"host": "192.168.0.91", "port": 1111})
    #protocol_url = (0, {"port": "com26", "baudrate":115200, "timeout":2, "writeTimeout":2})
    #protocol_url = (0, {"port": "/dev/ttyUSB0", "baudrate":115200, "timeout":2, "writeTimeout":2})
    lidar_url = ("192.168.0.91", 8080)
    #lidar_url = ("localhost", 8080)
    cb = CarBrain(protocol_url, lidar_url)
    cb.start()
    try:
        while 1:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    cb.stop()
        
        
        
        
        