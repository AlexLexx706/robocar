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
    import time
    port = Serial(port="com12", baudrate=256000)
    angle = 0.0
    print struct.unpack("<b", send_data(port, struct.pack("<Bf", 5, angle)))[0]
