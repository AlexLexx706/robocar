# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui, uic
import math
import logging

logger = logging.getLogger(__name__)

class RobotScene(QtGui.QGraphicsScene):
    def __init__(self, parent=None):
        super(QtGui.QGraphicsScene, self).__init__(parent)
        
        self.setSceneRect(-30000, -30000, 60000, 60000)
        self.wheel_base = 148.5
        self.wheel_diametr = 148.5
        self.robot_width = 220
        self.robot_length = 170

        self.first = True
        self.left_count = None
        self.right_count = None
        self.cur_pos = QtCore.QPointF(0,0)
        self.cur_path = QtGui.QPainterPath(QtCore.QPointF(0,0))
        self.path_item =  self.addPath(self.cur_path)
        self.robot_item = self.addRect(QtCore.QRectF(-self.robot_width / 2.0, -self.robot_length / 2.0 , self.robot_width, self.robot_length))
        rr = QtCore.QRectF(-self.robot_width / 2.0, -self.robot_width / 2.0 , self.robot_width, self.robot_width)
        self.start_item = self.addEllipse(rr, QtGui.QPen(QtGui.QColor(QtCore.Qt.red)))
        self.start_angle = 0.0
        self.follow = False
    
    def set_follow_robot(self, follow):
        self.follow = follow
    
    def update_robot_pos(self, pos, angle):
        self.robot_item.setPos(pos)
        self.robot_item.setRotation(angle/math.pi * 180)
        
        if not self.follow:
            self.views()[0].fitInView(self.itemsBoundingRect(), QtCore.Qt.KeepAspectRatio)
        else:
            self.views()[0].centerOn(pos)
            
    
    def clear_map(self):
        self.first = True
        self.cur_pos = QtCore.QPointF(0,0)
        self.cur_path = QtGui.QPainterPath(QtCore.QPointF(0,0))
        self.path_item.setPath(self.cur_path)
        self.update_robot_pos(QtCore.QPointF(0,0), 0)
        self.views()[0].fitInView(self.itemsBoundingRect(), QtCore.Qt.KeepAspectRatio)

    def update_wheel_count(self, left_count, right_count, angle):
        if self.first:
            self.first = False
            self.start_angle = angle
        else:
            #делаем шаг
            if self.left_count != left_count or self.right_count != right_count:
                left_encoder = (self.left_count - left_count) / 20.0 * math.pi * self.wheel_diametr
                right_encoder = (self.right_count - right_count) / 20.0 * math.pi * self.wheel_diametr

                distance = (left_encoder + right_encoder) / 2.0
                cur_angle = angle - self.start_angle
                
                #обновим путь.
                offset = QtCore.QPointF(distance * math.cos(cur_angle), distance * math.sin(cur_angle))
                self.cur_pos = self.cur_pos + offset
                self.cur_path.lineTo(self.cur_pos)
                self.path_item.setPath(self.cur_path)
                
                #обновим положение робота
                self.update_robot_pos(self.cur_pos, cur_angle)
        self.left_count = left_count
        self.right_count = right_count

            
        