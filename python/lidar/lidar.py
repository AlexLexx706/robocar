# -*- coding: utf-8 -*-
#!/usr/bin/python

import serial
import struct
import ultrasonic as us
import threading 
import Queue
from math import pi
import logging
import time
from pid import PID

logger = logging.getLogger(__name__)

class Lidar(threading.Thread):
    '''Читает данные с лидара'''
    PIN = 18
    
    def __init__(self, out_queue):
        '''Запускает лидар
        out_queue - выходная очередь данных сканирования, результаты формата:{{"angle": pi * 2, "values": [float,....] - значения в сантиметрах,
            всего 360} }
        '''
        threading.Thread.__init__(self)

        self.ser = serial.Serial("/dev/ttyAMA0", baudrate=115200, timeout=2)
        us.init()
        us.init_pwm({'range':256, 'freq':200, 'min':0.0, 'max':1.0})
        
        self.stop_flag = False
        self.out_queue = out_queue
        self.internal_queue = Queue.Queue()

        #смещение сектора от начала в градусах
        self.offset = 40

        #регулирование скорости пидом
        self.pid = PID()
        self.pid.SetKp(0.001)
        self.pid.SetKd(0.00007)
        #self.speed = 280.0
        self.speed = 260
        
        self.cur_speed = 0.0
        self.res = {}
        self.dt = 1.0 / 50.0
        
        self.fps = 0
        self.fps_counter = 0
        self.fps_time = time.time()
        
        
    
    def start(self):
        threading.Thread.start(self)
    
    def stop(self):
        self.stop_flag = True
        self.join()
    
    def speed_control_proc(self):
        while not self.stop_flag:
            error = self.speed - self.cur_speed
            out = self.pid.GenOut(error)
            value = us.get_pwm_data()["value"]
            value = value + out
            us.write_pwm(value)
            time.sleep(self.dt)
    
    def print_speed(self):
        while not self.stop_flag:
            print self.cur_speed
            time.sleep(self.dt*6)
            
    def checksum(self, data):
        """Compute and return the checksum as an int."""
        # group the data by word, little-endian
        data_list = []
        for t in range(10):
            data_list.append(ord(data[2 * t]) + (ord(data[2 * t + 1]) << 8) )
     
        # compute the checksum on 32 bits
        chk32 = 0
        for d in data_list:
            chk32 = (chk32 << 1) + d
     
        # return a value wrapped around on 15bits, and truncated to still fit into 15 bits
        checksum = (chk32 & 0x7FFF) + ( chk32 >> 15 ) # wrap around to fit into 15 bits
        checksum = checksum & 0x7FFF # truncate to 15 bits
        return int( checksum )
    
   
    def process_data(self, data):
        if len(data) != 22:
            logger.error("wrong packet length:{}".format(len(data)))
            return

        index, speed = struct.unpack("<BH", data[1:4])
        index = index - 0xA0
        self.cur_speed = speed / 64.
        self.res[index] = [self.cur_speed, []]
        
        #читаем измерения и силу сигнала
        self.res[index][1].append(struct.unpack("<HH", data[4:8]))
        self.res[index][1].append(struct.unpack("<HH", data[8:12]))
        self.res[index][1].append(struct.unpack("<HH", data[12:16]))
        self.res[index][1].append(struct.unpack("<HH", data[16:20]))
        check_summ = struct.unpack("<H", data[20:22])[0]
        

        if check_summ != self.checksum(data):
            logger.error("index:{} bad data!".format(index))

        #есть оборот
        if len(self.res) == 90:
            if self.out_queue is not None:
                values = []

                try:
                    for key in range(len(self.res)):
                        
                        for desc in self.res[key][1]:
                            values.append(desc[0] / 10.)
                    try:
                        #делаем смещение 
                        self.out_queue.put({"angle": pi * 2.0,
                                            "values": values if self.offset == 0 else
                                                [values[(i + int(self.offset)) % len(values)] for i in range(len(values))]}, block=False)
                    except Queue.Full:
                        logger.warning("Queue.Full")
                    
                except:
                    pass
            self.res = {}
            self.update_fps()


    def update_fps(self):
        self.fps_counter += 1
        cur_time = time.time()

        if cur_time > self.fps_time + 5:
            self.fps = self.fps_counter / (cur_time - self.fps_time)
            self.fps_time = cur_time
            self.fps_counter = 0
            logger.debug("fps:{}".format(self.fps))
        
    def run(self):
        try:
            logger.debug("->")
            #остановим лидар, прочитаем данные из буффера
            us.write_pwm(0)
            time.sleep(2)
            self.ser.flushInput()
            us.write_pwm(0.55)
            time.sleep(2)
            speed_control_thread = threading.Thread(target=self.speed_control_proc)
            speed_control_thread.start()
            self.fps_time = time.time()
            
            #threading.Thread(target=self.print_speed).start()

            while not self.stop_flag:
                ch = self.ser.read()
                #начало пакета
                if ch == "\xFA":
                    self.process_data(ch + self.ser.read(21))
        finally:
            speed_control_thread.join()
            us.disable_pwm()
            self.internal_queue.put(None)
            logger.debug("<-")

if __name__ == "__main__":
    logging.basicConfig(level=10, format="%(asctime)s %(levelname)s %(name)s::%(funcName)s %(message)s") 
    p = Lidar(None)
    p.start()
    try:
        raw_input("Pself.ress any key for exit")
    except KeyboardInterrupt:
        pass
    p.stop()
        
