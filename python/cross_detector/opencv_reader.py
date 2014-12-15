 # -*- coding: utf8 -*-
import cv2
import os
import logging

logger = logging.getLogger(__name__)

class OpencvReader:
    def __init__(self, dev_id=0):
        try:
            logger.debug("->")

            if os.name != 'nt':
                os.system("sudo pkill uv4l")
                os.system("sudo uv4l --driver raspicam --framerate 30 --nopreview yes --width 320 --height 240 --encoding h264 --auto-video_nr --rotation 180")

            self.cap = cv2.VideoCapture(dev_id)
        finally:
            logger.debug("<-")
        

    def read(self):
        ret = False
        try:
            #logger.debug("->")
            ret, frame =  self.cap.read()
            if ret:
                if frame.shape[0] != 240 and frame.shape[1] != 320:
                    frame = cv2.resize(frame, (320, 240))
        
            return ret, frame
        finally:
            #logger.debug("ret:{} <-".format(ret))
            pass

    def release(self):
        try:
            logger.debug("->")
            return self.cap.release()
        finally:
            logger.debug("<-")

if __name__ == "__main__":
    reader = OpencvReader()
    while 1:
        print "res:", reader.read()[0]
