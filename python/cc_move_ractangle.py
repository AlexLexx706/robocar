# -*- coding: utf-8 -*-
from car_controll.protocol import Protocol

def raad_protocol_mesages(res_queue):
    while 1:
        data = res_queue.get()
        
        if data is None:
            return 
        if data[0] == 0:
            print data[1]
            

if __name__ == "__main__":
    import time
    import math
    from Queue import Queue
    from threading import Thread
        
    #создадим поток для чтения сообщений из машины
    res_queue = Queue()
    rpm_thread = Thread(target=raad_protocol_mesages, args=(res_queue, ))
    rpm_thread.start()
    protocol = Protocol(res_queue)

    settings = {"port": "/dev/ttyUSB0",
                "baudrate": 115200,
                "timeout": 2,
                "writeTimeout": 2}
    
    #Создадим протокол и подключим его
    if protocol.connect(0, settings):
        print "Connected to: {}".format(settings["port"])
        time.sleep(3)
        
        #описывает прямоугольник
        c = 0
        try:
            while  c < 100:
                print "turn:", protocol.turn(math.pi /2)
                protocol.set_offset(0.5)
                time.sleep(2)
                protocol.set_offset(0.0)
                c += 1
        except KeyboardInterrupt:
            pass
        res_queue.put(None)
        rpm_thread.join()
        protocol.set_power_zerro()
        protocol.close()
        
        
        
        
        