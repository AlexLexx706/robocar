# -*- coding: utf-8 -*-
import serial
import struct
import logging

logger = logging.getLogger(__name__)

class Protocol:
    CMD_SET_LEFT_WHEEL_POWER = 0
    CMD_SET_RIGTH_WHEEL_POWER = 1
    CMD_PID_SETTINGS = 5
    CMD_ANGLE = 6
    CMD_ENABLE_DEBUG = 7
    CMD_SET_OFFSET = 8
    CMD_SET_WHEEL_SPEED = 9
    CMD_SET_SERVO_ANGLE = 10
    
    def __init__(self):
        self.serial = None
    
    def connect(self, port, speed):
        if self.serial is not None:
            self.serial.close()
        self.serial = None

        try:
            self.serial = serial.Serial(port, speed, timeout=4)
            return True
        except serial.SerialException as e:
            logger.error(e)
        return False

    def is_connected(self):
        return self.serial is not None

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
        

    def write(self, message):
        if self.serial is not None:
            self.serial.write(message)

    def read(self):
        if self.serial is not None:
            return self.serial.read()

    def close(self):
        if self.serial is not None:
            self.serial.close()
            self.serial = None

        