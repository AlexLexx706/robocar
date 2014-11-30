# -*- coding: utf-8 -*-
import serial
import struct
import logging
import threading
import time
import socket
from math import pi as PI
logger = logging.getLogger(__name__)

class TcpSerial:
    def __init__(self, host="192.168.0.91", port=1111):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((host, port))
        self.stop_flag = False
        
        
    def read(self, size=1):
        data = ""
        while not self.stop_flag and len(data) < size:
            data += self.s.recv(size - len(data))
        return data

    def write(self, data):
        self.s.send(data)
    
    def close(self):
        self.stop_flag = True
        self.s.shutdown(socket.SHUT_RDWR)
        self.s.close()
        

class Protocol:
    '''Реализация протокола управления машинкой'''
   
    CMD_SET_LEFT_WHEEL_POWER = 0
    CMD_SET_RIGTH_WHEEL_POWER = 1
    CMD_SET_WHEELS_POWER = 2
    CMD_SET_POWER_ZERRO = 3
    CMD_START_WALK = 4
    CMD_PID_SETTINGS = 5
    CMD_TURN = 6
    CMD_ENABLE_DEBUG = 7
    CMD_SET_POWER_OFFSET = 8
    CMD_SET_WHEEL_SPEED = 9
    CMD_SET_SERVO_ANGLE = 10
    CMD_SET_INFO_PERIOD = 11
    ACC_INFO = 12
   
    def __init__(self, result_queue=None):
        '''Реализация протокола управления машиной
            result_queue - получает сообщения передаваемые машиной, формат данных:
            (int - тип сообщения, data - данные сообщения)
            сечас два типа сообщений: 0 - текст, 1 - состояние датчиков.
        '''
        try:
            logger.debug("->")

            self.serial = None
            self.stop_read = True
            self.last_info = None
            self.sa_condition = threading.Condition()
            self.sa_res = None
            self.result_queue = result_queue
        finally:
            logger.debug("<-")
        
    def read_proc(self):
        '''
        Читает данные 
        '''
        try:
            logger.debug("read_proc ->")
            
            line = ""
            while not self.stop_read:
                s = self.serial.read()

                if len(s) > 0:
                    #начало приёма данных
                    if ord(s) == 0:
                        try:
                            size, acc = struct.unpack('<BB', self.serial.read(2))
                            data = self.serial.read(size-1)

                            #получили новые данные о состояние.
                            if acc == self.ACC_INFO:
                                self.last_info = struct.unpack('<fffhhhfllllBB', data)
                                if self.result_queue is not None:
                                    self.result_queue.put((1, self.last_info))
                            #завершение команды поворота
                            elif acc == self.CMD_TURN:
                                angle = -struct.unpack('<f', data)[0]
                                with self.sa_condition:
                                    self.sa_res = angle
                                    self.sa_condition.notify()
                                    

                        except Exception as e:
                            logging.error(str(e))
                    #отладка.
                    else:
                        if s != "\n":
                            line += s
                        else:
                            if self.result_queue is not None:
                                self.result_queue.put((0, line))
                            line = ""
        finally:
            logger.debug("read_proc <-")

    def connect(self, type, settings):
        '''type - тип транспорта 0 - com port, 1 - tcp socket
            settings - настройки:
                com_port:{"port": "com1", "baudrate":115200, "timeout":2, "writeTimeout":2}
                tcp_socket:{"host":"192.168.0.91", "port":1111}
        '''
        try:
            logger.debug("->")
            if self.serial is not None:
                self.serial.close()
            self.serial = None

            try:
                if type == 0:
                    self.serial = serial.Serial(**settings)
                else:
                    self.serial = TcpSerial(**settings)

                #запуск чтения.
                self.read_thread = threading.Thread(target=self.read_proc)
                self.stop_read = False
                self.read_thread.start()
                return True
            except serial.SerialException as e:
                logger.error(e)
            return False
        finally:
            logger.debug("<-")

    def close(self):
        try:
            logger.debug("->")
            if self.serial is not None:
                self.stop_read = True
                self.serial.close()
                self.read_thread.join()
                self.serial = None
        finally:
            logger.debug("<-")
        
    def is_connected(self):
        return self.serial is not None

    def set_wheels_power(self, l, r):
        if self.serial is not None:
            data = struct.pack("<Bff", self.CMD_SET_WHEELS_POWER, l, r)
            self.write(struct.pack("<B", len(data)) + data)
    
    def set_power_zerro(self):
        if self.serial is not None:
            data = struct.pack("<B", self.CMD_SET_POWER_ZERRO)
            self.write(struct.pack("<B", len(data)) + data)
    
    def start_walk(self):
        if self.serial is not None:
            data = struct.pack("<B", self.CMD_START_WALK)
            self.write(struct.pack("<B", len(data)) + data)

        
    def set_pid_settings(self, type, p, i, d):
        if self.serial is not None:
            data = struct.pack("<BBfff", self.CMD_PID_SETTINGS, type, p, i, d)
            self.write(struct.pack("<B", len(data)) + data)

    def turn(self, angle, angle_speed=PI / 180. * 90., no_wait=False):
        '''
        Повернуть на угол, комманда синхронная.
        angle - угол в рад., при значение > нуля - направление вращения корпуса против часовой стрелки,
                             при значение < нуля - направление вращения корпуса по часовой стрелке.
        angle_speed - скорость вращения рад./сек.
        #
        '''
        try:
            logger.debug("(angle:{} angle_speed:{})->".format(angle, angle_speed))
            
            #нельзя поворачивать на нуливой угол
            if angle == 0.0:
                return 0.0

            if self.serial is not None:
                with self.sa_condition:
                    self.sa_res = None

                data = struct.pack("<Bff", self.CMD_TURN, angle, angle_speed)
                self.write(struct.pack("<B", len(data)) + data)
                
                if not no_wait:
                    with self.sa_condition:
                        while self.sa_res is None:
                            self.sa_condition.wait()
                        return self.sa_res
        finally:
            logger.debug("<-")

    def set_offset(self, offset):
        '''
        Установить скорость движения машины.
        offset - скорость значение -1.0 - +1.0, положительное значение - движение вперёд, отрицательное движение назад. 
        '''
        try:
            logger.debug("(offset:{})->".format(offset))

            if self.serial is not None:
                data = struct.pack("<Bf", self.CMD_SET_POWER_OFFSET, offset)
                self.write(struct.pack("<B", len(data)) + data)
        finally:
            logger.debug("<-")
    
    def set_wheel_speed(self, id, speed):
        if self.serial is not None:
            data = struct.pack("<BBi", self.CMD_SET_WHEEL_SPEED, id, speed)
            self.write(struct.pack("<B", len(data)) + data)

    def set_servo_angle(self, id, angle):
        if self.serial is not None:
            data = struct.pack("<BBB", self.CMD_SET_SERVO_ANGLE, id, angle)
            self.write(struct.pack("<B", len(data)) + data)

    def set_left_wheel_power(self, value):
        if self.serial is not None:
            data = struct.pack("<Bf", self.CMD_SET_LEFT_WHEEL_POWER, value)
            self.write(struct.pack("<B", len(data)) + data)

    def set_right_wheel_power(self, value):
        if self.serial is not None:
            data = struct.pack("<Bf", self.CMD_SET_RIGTH_WHEEL_POWER, value)
            self.write(struct.pack("<B", len(data)) + data)
    
    def set_enable_debug(self, enable):
        if self.serial is not None:
            data = struct.pack("<BB", self.CMD_ENABLE_DEBUG, enable)
            self.write(struct.pack("<B", len(data)) + data)

    def set_info_period(self, period):
        if self.serial is not None:
            data = struct.pack("<BL", self.CMD_SET_INFO_PERIOD, period)
            self.write(struct.pack("<B", len(data)) + data)

    def write(self, message):
        if self.serial is not None:
            try:
                self.serial.write(message)
            except serial.SerialException as e:
                logger.error(str(e))

        