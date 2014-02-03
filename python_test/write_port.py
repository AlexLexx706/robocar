# -*- coding: utf-8 -*-
from serial import Serial
import time
import struct

def send_data(port, data):
    data = struct.pack("<b", len(data)) + data
    port.write(data)
    size = struct.unpack("<b", port.read())[0]
    return port.read(size)

if __name__ == '__main__':
    import math
    port = Serial(port="com9", baudrate=256000)
    while 1:
        value = math.cos(time.time()/2.0)
        #value = 0.3
        print struct.unpack("<b", send_data(port, struct.pack("<Bff", 2, 1, 1)))[0]
        #print struct.unpack("<b", send_data(port, struct.pack("<B", 3)))
        #print struct.unpack("<b", send_data(port, struct.pack("<Bf", 1, value)))[0]
