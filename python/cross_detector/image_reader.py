 # -*- coding: utf8 -*-
import cv2
import os
import logging
import time

logger = logging.getLogger(__name__)

class ImageReader:
    def __init__(self, file_path, fps=25):
        try:
            logger.debug("->")
            if isinstance(file_path, basestring):
                self.imgs = [cv2.imread(file_path,cv2.IMREAD_COLOR), ]
            else:
                self.imgs = []
                for f_p in file_path:
                    self.imgs.append(cv2.imread(f_p, cv2.IMREAD_COLOR))
            self.cur_index = 0
            self.fps = fps
            self.dt = 1.0 / self.fps
            self.cur_time = None

        finally:
            logger.debug("<-")
        

    def read(self):
        img = self.imgs[self.cur_index]
        self.cur_index = (self.cur_index + 1) % len(self.imgs)
        
        if img is None:
            return (False, None)
        
        if self.cur_time is None:
            self.cur_time = time.time()
        else:
            cur_time = time.time()
            dt = cur_time - self.cur_time

            if dt <= self.dt:
                time.sleep(self.dt - dt)
                self.cur_time = time.time()
            else:
                self.cur_time = time.time()
            
        return (True, img)

    def release(self):
        try:
            logger.debug("->")
            return True
        finally:
            logger.debug("<-")

if __name__ == "__main__":
    reader = ImageReader("../marker_no_circle.png")
    while 1:
        print "res:", reader.read()[0]
