# -*- coding: utf-8 -*-
import struct

def key_down_hendler(evt):
    global key_masks
    key_masks[evt.key] = True

def key_up_hendler(evt):
    global key_masks
    key_masks[evt.key] = False
    
def send_data(port, data):
    data = struct.pack("<b", len(data)) + data
    port.write(data)
    size = struct.unpack("<b", port.read())[0]
    return port.read(size)

def servo_process(cmd_queue):
    from serial import Serial
    import time
    port = Serial(port="com9", baudrate=256000)
    
    while 1:
        l, r = cmd_queue.get()

        if (l != 0) or (r != 0):
            print struct.unpack("<B", send_data(port, struct.pack("<Bff", 2, l, r)))[0]
        else:
            print struct.unpack("<B", send_data(port, struct.pack("<B", 3)))[0]

if __name__ == '__main__':
    import multiprocessing
    from visual import *

    scene = display(x=0, y=0, width= 500, height= 500)
    box()

    key_masks = {"w": False,
                 "s": False,
                 "a": False,
                 "d": False}

    scene.bind('keydown', key_down_hendler)
    scene.bind('keyup', key_up_hendler)
    max_speed = 0.6
    
    cmd_queue = multiprocessing.Queue()
    proc = multiprocessing.Process(target=servo_process,  args=(cmd_queue,))
    proc.start()

    
    while True:
        rate(30)
        l = 0.0
        r = 0.0
        
        #вперёд
        if key_masks["w"]:
            l = -max_speed
            r = -max_speed
        #назад
        elif key_masks["s"]:
            l = max_speed
            r = max_speed

            #лево
        if key_masks["a"]:
            if (l > 0):
                l = max_speed * 0.2
            elif  (l < 0 ):
                l = -max_speed * 0.2
            else:
                r = -max_speed * 0.5
        #право
        elif key_masks["d"]:
            if (r > 0):
                r = max_speed * 0.2
            elif  (r < 0 ):
                r = -max_speed * 0.2
            else:
                l = -max_speed * 0.5
        cmd_queue.put([l, r])
           