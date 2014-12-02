# -*- coding: utf-8 -*-
from car_controll.protocol import Protocol
import time
# -*- coding: utf-8 -*-
import math
from Queue import Queue
from threading import Thread
from threading import Lock
from tcp_rpc.client import Client
from lidar.LineFeaturesMaker import LineFeaturesMaker
import logging

USE_GUI = True

class CarBrain(Thread):
    def __init__(self, protocol_url=(1, {"host":"192.168.0.91", "port":1111}), lidar_url=("192.168.0.91", 8080)):
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

    def get_hole(self):
        with self.hole_lock:
            return self.hole
    
    def start(self):
        #if self.protocol.connect(*self.protocol_url):
        #    print "Connected to: {}".format(self.protocol_url)
        if 1:

            #отображалка
            if USE_GUI:
                import multiprocessing
                from LidarFrame import main
                self.data_queue_for_gui = multiprocessing.Queue()
                multiprocessing.Process(target=main, args=(self.data_queue_for_gui,)).start()

            self.rpm_thread.start()
            self.lidar_thread.start()
            Thread.start(self)

    def run(self):
        while not self.stop_flag:
            time.sleep(1)
        return

        #поток управления машиной.
        angle_speed = math.pi * 0.7
        self.protocol.set_pid_settings(0, 2, 0.2, 0.1)
        self.protocol.set_offset(0.4)

        while not self.stop_flag:
            if 1:
                hole = self.get_hole()

                if hole is not None:
                    angle = -(90. - hole["angle"]) /180. * math.pi
                    print "Turn to clasters:", hole["clasters"], " angle:", angle
                    self.protocol.turn(angle, angle_speed, True)
                else:
                    print "Turn 90!!!"
                    self.protocol.turn(math.pi / 2.0, angle_speed, True)
            time.sleep(0.5)

    def rpm_proc(self):
        while 1:
            data = self.res_queue.get()
            
            if data is None:
                return 

            if data[0] == 0:
                #print data[1]
                pass

    def lidar_proc(self ):
        client = Client(self.lidar_url)

        while 1:
            data = client.ik_get_sector(1)[0]

            #1. найдём кластеры точек
            lines = self.lfm.clusters_to_lines(self.lfm.sector_to_lines_clusters(data))

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

                #Отправим в отображалку
                if USE_GUI:
                    primitives = [{"line": l, "color": (0, 255, 0)} for l in lines]

                    if len(holes):
                        primitives.append({"line": holes[0], "color":(255, 0, 0)})

                    self.data_queue_for_gui.put(primitives)

               #print len(holes),  " ".join(["({} {})".format(c["clasters"][0], c["clasters"][1]) for c in holes])


if __name__ == "__main__":
    logging.getLogger("protocol").setLevel(50)

    protocol_url = (1, {"host": "192.168.10.154", "port": 1111})
    lidar_url = ("192.168.10.154", 8080)

    cb = CarBrain(protocol_url, lidar_url)
    cb.start()
    cb.join()
        
        
        
        
        