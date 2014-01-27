
if __name__ == '__main__':
    import multiprocessing
    from visual import *
    from serial import Serial
    import struct

    serial = Serial(port="com6", baudrate=115200)
                   
    scene = display(x=0,
                    y=0,
                    width= 200,
                    height= 200)
    box()
                    
                    
    key_masks = {}

    def key_down_hendler(evt):
        global key_masks
        key_masks[evt.key] = True

    def key_up_hendler(evt):
        global key_masks
        key_masks[evt.key] = False
        
    scene.bind('keydown', key_down_hendler)
    scene.bind('keyup', key_up_hendler)
    key_masks["w"] = False
    key_masks["s"] = False
    key_masks["a"] = False
    key_masks["d"] = False
    while True:
        rate(30)
        l = 0
        r = 0

        if key_masks["w"]:
            l = 2
            r = 2
        elif key_masks["s"]:
            l = 1
            r = 1

        if key_masks["a"]:
            if not key_masks["s"]:
                l = 0
                r = 2
            else:
                l = 0
                r = 1
        elif key_masks["d"]:
            if not key_masks["s"]:
                l = 2
                r = 0
            else:
                l = 1
                r = 0

        serial.write(struct.pack("<B", (l << 2 | r)))
