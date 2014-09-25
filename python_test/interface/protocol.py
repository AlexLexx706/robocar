# -*- coding: utf-8 -*-
import serial
import struct
import logging
import threading
from PyQt4 import QtCore
from PyQt4.QtCore import pyqtSignal

logger = logging.getLogger(__name__)

class Protocol(QtCore.QObject):
    add_line = pyqtSignal(str)
    update_info = pyqtSignal(object)
    
    CMD_SET_LEFT_WHEEL_POWER = 0
    CMD_SET_RIGTH_WHEEL_POWER = 1
    CMD_SET_WHEELS_POWER = 2
    CMD_SET_POWER_ZERRO = 3
    CMD_START_WALK = 4
    CMD_PID_SETTINGS = 5
    CMD_ANGLE = 6
    CMD_ENABLE_DEBUG = 7
    CMD_SET_OFFSET = 8
    CMD_SET_WHEEL_SPEED = 9
    CMD_SET_SERVO_ANGLE = 10
    CMD_SET_INFO_PERIOD = 11
    ACC_INFO = 12
   
    def __init__(self):
        QtCore.QObject.__init__(self)

        self.serial = None
        self.stop_read = True
        
    def read_proc(self):
        try:
            logger.debug("read_proc ->")
            
            line = ""
            while not self.stop_read:
                s = self.read()

                if len(s) > 0:
                    #начало приёма данных
                    if ord(s) == 0:
                        size, acc = struct.unpack('<BB', self.read(2))
                        data = self.read(size-1)
                        
                        #получили новые данные о состояние.
                        if acc == self.ACC_INFO:
                            self.update_info.emit(struct.unpack('<fffffflHHBB', data))
                    #отладка.
                    else:
                        if s != "\n":
                            line += s
                        else:
                            self.add_line.emit(line)
                            line = ""
        finally:
            logger.debug("read_proc <-")

    def connect(self, port, speed):
        if self.serial is not None:
            self.serial.close()
        self.serial = None

        try:
            self.serial = serial.Serial(port, speed, timeout=4)

            #запуск чтения.
            self.read_thread = threading.Thread(target=self.read_proc)
            self.stop_read = False
            self.read_thread.start()
            return True
        except serial.SerialException as e:
            logger.error(e)
        return False

    def close(self):
        if self.serial is not None:
            self.stop_read = True
            self.serial.close()
            self.read_thread.join()
            self.serial = None
        
    def is_connected(self):
        return self.serial is not None

    def set_wheels_power(self, l, r):
        if self.serial is not None:
            data = struct.pack("<Bff", self.CMD_SET_WHEELS_POWER, l, r)
            self.serial.write(struct.pack("<B", len(data)) + data)
    
    def set_power_zerro(self):
        if self.serial is not None:
            data = struct.pack("<B", self.CMD_SET_POWER_ZERRO)
            self.serial.write(struct.pack("<B", len(data)) + data)
    
    def start_walk(self):
        if self.serial is not None:
            data = struct.pack("<B", self.CMD_START_WALK)
            self.serial.write(struct.pack("<B", len(data)) + data)

        
    def set_pid_settings(self, type, p, i, d):
        if self.serial is not None:
            data = struct.pack("<BBfff", self.CMD_PID_SETTINGS, type, p, i, d)
            self.serial.write(struct.pack("<B", len(data)) + data)

    def set_angle(self, angle):
        if self.serial is not None:
            data = struct.pack("<Bf", self.CMD_ANGLE, angle)
            self.serial.write(struct.pack("<B", len(data)) + data)
    
    def set_wheel_speed(self, id, speed):
        if self.serial is not None:
            data = struct.pack("<BBi", self.CMD_SET_WHEEL_SPEED, id, speed)
            self.serial.write(struct.pack("<B", len(data)) + data)

    def set_servo_angle(self, id, angle):
        if self.serial is not None:
            data = struct.pack("<BBB", self.CMD_SET_SERVO_ANGLE, id, angle)
            self.serial.write(struct.pack("<B", len(data)) + data)

    def set_left_wheel_power(self, value):
        if self.serial is not None:
            data = struct.pack("<Bf", self.CMD_SET_LEFT_WHEEL_POWER, value)
            self.serial.write(struct.pack("<B", len(data)) + data)

    def set_right_wheel_power(self, value):
        if self.serial is not None:
            data = struct.pack("<Bf", self.CMD_SET_RIGTH_WHEEL_POWER, value)
            self.serial.write(struct.pack("<B", len(data)) + data)
    
    def set_enable_debug(self, enable):
        if self.serial is not None:
            data = struct.pack("<BB", self.CMD_ENABLE_DEBUG, enable)
            self.serial.write(struct.pack("<B", len(data)) + data)

    def set_offset(self, offset):
        if self.serial is not None:
            data = struct.pack("<Bf", self.CMD_SET_OFFSET, offset)
            self.serial.write(struct.pack("<B", len(data)) + data)

    def set_info_period(self, period):
        if self.serial is not None:
            data = struct.pack("<BL", self.CMD_SET_INFO_PERIOD, period)
            self.serial.write(struct.pack("<B", len(data)) + data)

    def write(self, message):
        if self.serial is not None:
            self.serial.write(message)

    def read(self, size=1):
        if self.serial is not None:
            return self.serial.read(size)

        