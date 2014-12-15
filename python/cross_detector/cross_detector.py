 # -*- coding: utf8 -*-
import numpy as np
import cv2
import math
import threading
import time
import os
import logging
import traceback
import glob
from opencv_reader import OpencvReader
from Vec2d import Vec2d
import sys
from line_reducer import LineReducer

logger = logging.getLogger(__name__)
import random

class CrossDetector(threading.Thread):
    NO_BORDER = 0
    BLACK_BORDER = 1
    WHITE_BORDER = 2
    BORDERS_TYPES = [NO_BORDER, BLACK_BORDER, WHITE_BORDER]
    
    def __init__(self, visible, reader):
        try:
            logger.debug("->")
            threading.Thread.__init__(self)
            self.visible = visible
            self.marker_state = None
            self.lock = threading.Lock()
            self.fps = 0
            self.f_count = 0
            self.stop_flag = False
            self.reader = reader

            self.hl_min_line_length = 150
            self.hl_max_line_gap = 20
            self.hl_threshold = 83

            self.at_block_size = 15

            self.r_angle = 10        
            self.r_h = 6
            self.r_distance = 6
            self.r_short = 10
            
            self.c_distance = 6
            self.lr = LineReducer()
        finally:
            logger.debug("<-")
    
    def stop(self):
        self.stop_flag = True
    
    def get_marker_state(self):
        '''Возвращает состояние маркера
        Результат: None - нет маркера или 
            {"color": string, цвет маркера: black или wight,
             "center": tuple of float (x,y), положение центра креста в кадре, значение нормированно от 0.0-1.0 }
        '''
        with self.lock:
            if self.marker_state is None:
                return None
            return dict(self.marker_state)
    
    def get_fps(self):
        return self.fps

    def check_color(self, gray, cross):
        pos = Vec2d(0,0)

        for pair in cross:
            pos += pair[3][0]
        pos /= len(cross)

        size = 1
        x = int(pos.x)
        y = int(pos.y)
        rect = gray[y - size: y + size + 1, x - size: x + size + 1]
        color = rect.sum() / rect.size
        return (pos, color)

    def process(self, frame):
        try:
            #logger.debug("->")
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray,(5,5),0)
            th = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, self.at_block_size, 10)
            lines = cv2.HoughLinesP(th, 1, np.pi / 180, self.hl_threshold, self.hl_min_line_length, self.hl_max_line_gap)
            cross_lines = []
            new_lines = []
            bas_lines = []

            if lines is not None:
                #1. рассчёт признаков
                bas_lines = [self.lr.create_line_attributes(pos) for pos in lines[0]]
                
                #2ю группируем линии по направлению и близости.
                new_lines = self.lr.reduce(bas_lines, max_angle=self.r_angle, max_h=self.r_h, max_distance=self.r_distance, short_lines=self.r_short)
                cross_lines = self.lr.check_cross_2(new_lines, max_distance=self.c_distance)

                #нет крестов
                if len(cross_lines) == 0:
                    with self.lock:
                        self.marker_state = None
                #кресты обнаружены
                else:
                    #вычислим цвет
                    color_data = self.check_color(gray, cross_lines[0])

                    with self.lock:
                        self.marker_state = {"color": "white" if color_data[1] > 150 else "black",
                                             "center":(color_data[0][0] / float(frame.shape[1]),
                                                       color_data[0][1] / float(frame.shape[0]))}
            #отображение
            if self.visible:
                self.hl_min_line_length = cv2.getTrackbarPos('hl_length','frame')
                self.hl_min_line_length = self.hl_min_line_length if self.hl_min_line_length > 10 else 10
                self.hl_max_line_gap = cv2.getTrackbarPos('hl_gap','frame')
                self.hl_max_line_gap = self.hl_max_line_gap if self.hl_max_line_gap > 10 else 10
                self.hl_threshold = cv2.getTrackbarPos('hl_thres','frame')
                self.hl_threshold = self.hl_threshold if self.hl_threshold > 10 else 10

                self.at_block_size = cv2.getTrackbarPos('at_size','frame')
                self.at_block_size = self.at_block_size if self.at_block_size >= 3 else 3
                self.at_block_size = self.at_block_size if self.at_block_size % 2 == 1 else self.at_block_size + 1

                self.r_angle = cv2.getTrackbarPos('r_angle','frame')
                self.r_h = cv2.getTrackbarPos('r_h','frame')
                self.r_distance = cv2.getTrackbarPos('r_distance','frame')
                self.r_short = cv2.getTrackbarPos('r_short','frame')
                self.c_distance = cv2.getTrackbarPos('c_distance','frame')


                cv2.putText(frame, "fps: {}".format(self.fps), (0,30), self.font, 1, (0, 0, 255), 2, 1)

                colors = [(0, 0 , 255),(0, 255 , 0),(0, 0 , 255), (255, 255 , 0), (0, 255 , 255), (255, 255 , 255),
                          (0,0,0)]


                for i, cross in enumerate(cross_lines):
                    color = colors[i % len(colors)]

                    for pair in cross:
                        data = pair[0]
                        p1 = (int(data["pos"][0]), int(data["pos"][1]))
                        p2 = (int(data["end"][0]), int(data["end"][1]))
                        cv2.line(frame, p1, p2, color, 2)

                        data = pair[1]
                        p1 = (int(data["pos"][0]), int(data["pos"][1]))
                        p2 = (int(data["end"][0]), int(data["end"][1]))
                        cv2.line(frame, p1, p2, color, 2)

                    color_data = self.check_color(gray, cross)
                    cv2.putText(frame, "color {}".format("white" if color_data[1] > 150 else "black"),
                                (int(color_data[0][0]), int(color_data[0][1])), self.font, 1, (255,255,255), 2, 1)

                frame2 = np.zeros(frame.shape, np.int8)
                frame3 = np.zeros(frame.shape[:2], np.int8)

                for i, data in enumerate(new_lines):
                    p1 = (int(data["pos"][0]), int(data["pos"][1]))
                    p2 = (int(data["end"][0]), int(data["end"][1]))
                    p_t = p1

                    cv2.line(frame2, p1, p2, colors[i % len(colors)], 2)

                for i, data in enumerate(bas_lines):
                    p1 = (int(data["pos"][0]), int(data["pos"][1]))
                    p2 = (int(data["end"][0]), int(data["end"][1]))
                    cv2.line(frame3, p1, p2, (255,), 1)

                cv2.imshow('frame', frame)
                cv2.imshow('frame2', frame2)
                cv2.imshow('frame3', frame3)
                cv2.imshow("th", th)
        finally:
            #logger.debug("<-")
            pass

    def init_draw(self):
        try:
            logger.debug("->")

            if self.visible:
                self.init_sliders = True
                self.font = cv2.FONT_HERSHEY_SIMPLEX

                def nothing(x):
                    pass

                cv2.namedWindow('frame', flags=cv2.WINDOW_AUTOSIZE)
                cv2.createTrackbar('hl_length','frame', self.hl_min_line_length, 255, nothing)
                cv2.createTrackbar('hl_gap','frame', self.hl_max_line_gap, 100, nothing)
                cv2.createTrackbar('hl_thres','frame', self.hl_threshold, 100, nothing)

                cv2.createTrackbar('at_size','frame', self.at_block_size, 30, nothing)
                
                cv2.createTrackbar('r_angle','frame', self.r_angle, 30, nothing)
                cv2.createTrackbar('r_h','frame', self.r_h, 30, nothing)
                cv2.createTrackbar('r_distance','frame', self.r_distance, 30, nothing)
                cv2.createTrackbar('r_short','frame', self.r_short, 30, nothing)

                cv2.createTrackbar('c_distance','frame', self.c_distance, 40, nothing)
        finally:
            logger.debug("<-")
           
            
    def run(self):
        try:
            logger.debug("->")

            start_time = time.time()
            f_count = 0
            self.init_draw()

            #алгоритм выделения креста!!!!
            try:
                while (not self.stop_flag):
                    ret, frame = self.reader.read()

                    if ret:
                        self.process(frame)
                        f_count += 1

                        #подсчёт fps
                        if  time.time() > start_time + 1:
                            self.fps = f_count / 1
                            start_time = time.time()
                            f_count = 0
                            logger.info("fps:{}".format(self.fps))

                        if self.visible:
                            if cv2.waitKey(5) & 0xFF == 27:
                                break
            except KeyboardInterrupt:
                pass
            except:
                logger.error(traceback.format_exc())

            #When everything done, release the capture
            self.reader.release()

            if self.visible:
                cv2.destroyAllWindows()
        finally:
            logger.debug("<-")


if __name__ == "__main__":
    import cProfile
    import sys
    logging.basicConfig(level=10, format="%(name)s::%(funcName)s %(message)s")
    logging.getLogger("line_reducer").setLevel(100)
    detector = CrossDetector(True, reader=OpencvReader())
    #cProfile.run("detector.run()")
    #sys.exit(1)
    
    detector.start()

    try:
        while 1:
            time.sleep(3)
            print "state:", detector.get_marker_state()
            print "fps:", detector.get_fps()
    except KeyboardInterrupt:
        detector.stop()