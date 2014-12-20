#!/usr/bin/python 
# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import pyqtSlot, pyqtSignal
import os
import logging
import math

try:
    import right_wall_lidar_motion
except:
    import sys
    sys.path.append("..")
    import right_wall_lidar_motion

logger = logging.getLogger(__name__)

class AlgControls(QtGui.QGroupBox):

    def __init__(self, settings):
        QtGui.QGroupBox.__init__(self)
        uic.loadUi(os.path.join(os.path.split(__file__)[0], "alg_controls.ui"), self)
        self.toggled.connect(self.on_toggled)
        self.update_control_angle = None        
        self.settings = settings


        self.blockSignals(True)
        self.doubleSpinBox_DELTA.blockSignals(True)
        self.doubleSpinBox_WALL_ANALYSIS_DX_GAP.blockSignals(True)
        self.doubleSpinBox_WALL_ANALYSIS_ANGLE.blockSignals(True)
        self.doubleSpinBox_MIN_LIDAR_DISTANCE.blockSignals(True)
        self.doubleSpinBox_MAX_LIDAR_DISTANCE.blockSignals(True)
        self.doubleSpinBox_TRUSTABLE_LIDAR_DISTANCE.blockSignals(True)
        self.doubleSpinBox_MIN_GAP_WIDTH.blockSignals(True)
        self.doubleSpinBox_Dr.blockSignals(True)
        self.doubleSpinBox_Da.blockSignals(True)
        self.doubleSpinBox_Dh.blockSignals(True)


        self.settings.beginGroup("lidar_alg")
        self.setChecked(self.settings.value("show", True).toBool())
        self.doubleSpinBox_DELTA.setValue(self.settings.value("DELTA", 70.0).toDouble()[0])
        self.doubleSpinBox_WALL_ANALYSIS_DX_GAP.setValue(self.settings.value("WALL_ANALYSIS_DX_GAP", 15).toDouble()[0])
        self.doubleSpinBox_WALL_ANALYSIS_ANGLE.setValue(self.settings.value("WALL_ANALYSIS_ANGLE", 90).toDouble()[0])
        self.doubleSpinBox_MIN_LIDAR_DISTANCE.setValue(self.settings.value("MIN_LIDAR_DISTANCE", 20).toDouble()[0])
        self.doubleSpinBox_MAX_LIDAR_DISTANCE.setValue(self.settings.value("MAX_LIDAR_DISTANCE", 600).toDouble()[0])
        self.doubleSpinBox_TRUSTABLE_LIDAR_DISTANCE.setValue(self.settings.value("TRUSTABLE_LIDAR_DISTANCE", 400).toDouble()[0])
        self.doubleSpinBox_MIN_GAP_WIDTH.setValue(self.settings.value("MIN_GAP_WIDTH", 50).toDouble()[0])
        self.doubleSpinBox_Dr.setValue(self.settings.value("Dr", 30).toDouble()[0])
        self.doubleSpinBox_Da.setValue(self.settings.value("Da", 0.1).toDouble()[0])
        self.doubleSpinBox_Dh.setValue(self.settings.value("Dh", 0.70).toDouble()[0])
        self.doubleSpinBox_MIN_GAP_ANGLE.setValue(self.settings.value("MIN_GAP_ANGLE", 0.0628).toDouble()[0])
        self.settings.endGroup()

        self.blockSignals(False)
        self.doubleSpinBox_DELTA.blockSignals(False)
        self.doubleSpinBox_WALL_ANALYSIS_DX_GAP.blockSignals(False)
        self.doubleSpinBox_WALL_ANALYSIS_ANGLE.blockSignals(False)
        self.doubleSpinBox_MIN_LIDAR_DISTANCE.blockSignals(False)
        self.doubleSpinBox_MAX_LIDAR_DISTANCE.blockSignals(False)
        self.doubleSpinBox_TRUSTABLE_LIDAR_DISTANCE.blockSignals(False)
        self.doubleSpinBox_MIN_GAP_WIDTH.blockSignals(False)
        self.doubleSpinBox_Dr.blockSignals(False)
        self.doubleSpinBox_Da.blockSignals(False)
        self.doubleSpinBox_Dh.blockSignals(False)
        right_wall_lidar_motion.init()


    def draw_alg(self, data):
        if self.isChecked() and data is not None:
            right_wall_lidar_motion.MIN_GAP_ANGLE = self.doubleSpinBox_MIN_GAP_ANGLE.value()
            right_wall_lidar_motion.DELTA = self.doubleSpinBox_DELTA.value()
            right_wall_lidar_motion.WALL_ANALYSIS_DX_GAP = self.doubleSpinBox_WALL_ANALYSIS_DX_GAP.value()
            right_wall_lidar_motion.WALL_ANALYSIS_ANGLE = int(self.doubleSpinBox_WALL_ANALYSIS_ANGLE.value())
            right_wall_lidar_motion.MIN_LIDAR_DISTANCE = self.doubleSpinBox_MIN_LIDAR_DISTANCE.value()
            right_wall_lidar_motion.MAX_LIDAR_DISTANCE = self.doubleSpinBox_MAX_LIDAR_DISTANCE.value()
            right_wall_lidar_motion.TRUSTABLE_LIDAR_DISTANCE = self.doubleSpinBox_TRUSTABLE_LIDAR_DISTANCE.value()

            right_wall_lidar_motion.MIN_GAP_WIDTH = self.doubleSpinBox_MIN_GAP_WIDTH.value()

            right_wall_lidar_motion.Dr = self.doubleSpinBox_Dr.value()
            right_wall_lidar_motion.Da = self.doubleSpinBox_Da.value()
            right_wall_lidar_motion.Dh = self.doubleSpinBox_Dh.value()
            
            move_res = right_wall_lidar_motion.move(data)
            
            if move_res is not None and 'primitives' in move_res:
                dir_dist = 100
                dir_line = {"line": {'pos':(0,0),
                                     'end': (dir_dist * math.cos(math.pi / 2.0 + move_res['turn_angle']),
                                             dir_dist * math.sin(math.pi / 2.0 + move_res['turn_angle']))},
                           "color":(0, 255, 0)}
                move_res["primitives"].append(dir_line)
                
                #Добавим в алгоритм управления данные
                if self.update_control_angle is not None:
                    self.update_control_angle(move_res['turn_angle'])
                
                return move_res["primitives"]
        return []


    #######################################################
    @pyqtSlot("bool")
    def on_toggled(self, value):
        self.settings.beginGroup("lidar_alg")
        self.settings.setValue("show", value)
        self.settings.endGroup()

    @pyqtSlot("double")
    def on_doubleSpinBox_DELTA_valueChanged(self, value):
        self.settings.beginGroup("lidar_alg")
        self.settings.setValue("DELTA", value)
        self.settings.endGroup()

    @pyqtSlot("double")
    def on_doubleSpinBox_WALL_ANALYSIS_DX_GAP_valueChanged(self, value):
        self.settings.beginGroup("lidar_alg")
        self.settings.setValue("WALL_ANALYSIS_DX_GAP", value)
        self.settings.endGroup()

    @pyqtSlot("double")
    def on_doubleSpinBox_WALL_ANALYSIS_ANGLE_valueChanged(self, value):
        self.settings.beginGroup("lidar_alg")
        self.settings.setValue("WALL_ANALYSIS_ANGLE", value)        
        self.settings.endGroup()

    @pyqtSlot("double")
    def on_doubleSpinBox_MIN_LIDAR_DISTANCE_valueChanged(self, value):
        self.settings.beginGroup("lidar_alg")
        self.settings.setValue("MIN_LIDAR_DISTANCE", value) 
        self.settings.endGroup()

    @pyqtSlot("double")
    def on_doubleSpinBox_MAX_LIDAR_DISTANCE_valueChanged(self, value):
        self.settings.beginGroup("lidar_alg")
        self.settings.setValue("MAX_LIDAR_DISTANCE", value) 
        self.settings.endGroup()
   
    @pyqtSlot("double")
    def on_doubleSpinBox_TRUSTABLE_LIDAR_DISTANCE_valueChanged(self, value):
        self.settings.beginGroup("lidar_alg")
        self.settings.setValue("TRUSTABLE_LIDAR_DISTANCE", value) 
        self.settings.endGroup()

    @pyqtSlot("double")
    def on_doubleSpinBox_MIN_GAP_WIDTH_valueChanged(self, value):
        self.settings.beginGroup("lidar_alg")
        self.settings.setValue("MIN_GAP_WIDTH", value) 
        self.settings.endGroup()

    @pyqtSlot("double")
    def on_doubleSpinBox_Dr_valueChanged(self, value):
        self.settings.beginGroup("lidar_alg")
        self.settings.setValue("Dr", value) 
        self.settings.endGroup()

    @pyqtSlot("double")
    def on_doubleSpinBox_Da_valueChanged(self, value):
        self.settings.beginGroup("lidar_alg")
        self.settings.setValue("Da", value)
        self.settings.endGroup()
        
    @pyqtSlot("double")
    def on_doubleSpinBox_Dh_valueChanged(self, value):
        self.settings.beginGroup("lidar_alg")
        self.settings.setValue("Dh", value)        
        self.settings.endGroup()
        
    @pyqtSlot("double")
    def on_doubleSpinBox_MIN_GAP_ANGLE_valueChanged(self, value):
        self.settings.beginGroup("lidar_alg")
        self.settings.setValue("MIN_GAP_ANGLE", value)
        self.settings.endGroup()    

