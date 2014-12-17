#!/usr/bin/python 
# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import pyqtSlot, pyqtSignal
from lidar.LineFeaturesMaker import LineFeaturesMaker
import os
import math
import logging

logger = logging.getLogger(__name__)

class SectorControls(QtGui.QGroupBox):

    def __init__(self, settings):
        QtGui.QGroupBox.__init__(self)
        uic.loadUi(os.path.join(os.path.split(__file__)[0], "sector_controls.ui"), self)
        self.toggled.connect(self.on_toggled)
        self.lfm = LineFeaturesMaker()
        self.settings = settings

        self.blockSignals(True)
        self.doubleSpinBox_start_angle.blockSignals(True)
        self.doubleSpinBox_max_radius.blockSignals(True)
        self.groupBox_show_points.blockSignals(True)
        self.groupBox_show_clusters.blockSignals(True)
        self.spinBox_clasters_size.blockSignals(True)
        self.doubleSpinBox_max_offset.blockSignals(True)
        self.spinBox_min_cluster_len.blockSignals(True)
        self.checkBox_show_points_clusters.blockSignals(True)
        self.groupBox_show_lines_clusters.blockSignals(True)
        self.doubleSpinBox_split_threshold.blockSignals(True)
        self.doubleSpinBox_merge_threshold.blockSignals(True)
        self.checkBox_show_line_cluster_points.blockSignals(True)
        self.checkBox_show_line_cluster_lines.blockSignals(True)

        self.settings.beginGroup("lidar_sector")
        self.setChecked(self.settings.value("show", True).toBool())
        self.doubleSpinBox_start_angle.setValue(self.settings.value("start_angle", 1.57).toDouble()[0])
        self.doubleSpinBox_max_radius.setValue(self.settings.value("max_radius", 1000).toInt()[0])
        self.groupBox_show_points.setChecked(self.settings.value("points", True).toBool())
        self.groupBox_show_clusters.setChecked(self.settings.value("show_clusters", True).toBool())
        self.spinBox_clasters_size.setValue(self.settings.value("clasters_size", 3).toInt()[0])
        self.doubleSpinBox_max_offset.setValue(self.settings.value("max_offset", 30.0).toDouble()[0])
        self.spinBox_min_cluster_len.setValue(self.settings.value("min_cluster_len", 0).toInt()[0])
        self.checkBox_show_points_clusters.setChecked(self.settings.value("show_points_clusters", True).toBool())
        self.groupBox_show_lines_clusters.setChecked(self.settings.value("show_lines_clusters", True).toBool())
        self.doubleSpinBox_split_threshold.setValue(self.settings.value("split_threshold", 2.0).toDouble()[0])
        self.doubleSpinBox_merge_threshold.setValue(self.settings.value("merge_threshold", 10).toDouble()[0])
        self.checkBox_show_line_cluster_points.setChecked(self.settings.value("show_line_cluster_points", True).toBool())
        self.checkBox_show_line_cluster_lines.setChecked(self.settings.value("show_line_cluster_lines", True).toBool())
        self.settings.endGroup()

        self.blockSignals(False)
        self.doubleSpinBox_start_angle.blockSignals(False)
        self.doubleSpinBox_max_radius.blockSignals(False)
        self.groupBox_show_points.blockSignals(False)
        self.groupBox_show_clusters.blockSignals(False)
        self.spinBox_clasters_size.blockSignals(False)
        self.doubleSpinBox_max_offset.blockSignals(False)
        self.spinBox_min_cluster_len.blockSignals(False)
        self.checkBox_show_points_clusters.blockSignals(False)
        self.groupBox_show_lines_clusters.blockSignals(False)
        self.doubleSpinBox_split_threshold.blockSignals(False)
        self.doubleSpinBox_merge_threshold.blockSignals(False)
        self.checkBox_show_line_cluster_points.blockSignals(False)
        self.checkBox_show_line_cluster_lines.blockSignals(False)



    
    def draw_clusters(self, data):
        primetives = []
        
        if self.isChecked():
            points = self.lfm.sector_to_points(data,
                                                start_angle=self.doubleSpinBox_start_angle.value(),
                                                max_radius=self.doubleSpinBox_max_radius.value())
            if self.groupBox_show_points.isChecked():
                primetives.append({"points": points, "color":(255, 0, 0), "size": self.spinBox_points_size.value()})

            #2. найдём кластеры линий.
            if self.groupBox_show_clusters.isChecked():
                #Кластеры точек
                if self.checkBox_show_points_clusters.isChecked():
                    clasters = self.lfm.sector_to_points_clusters(points,
                                                max_offset = self.doubleSpinBox_max_offset.value(),
                                                min_cluster_len=self.spinBox_min_cluster_len.value(),
                                                start_angle=self.doubleSpinBox_start_angle.value(),
                                                max_radius=self.doubleSpinBox_max_radius.value())
                    for i, c in enumerate(clasters):
                        color = QtGui.QColor(QtCore.Qt.GlobalColor(3+i%19)).getRgb()[:-1]
                        primetives.append({"points": c, "color": color, "size": self.spinBox_clasters_size.value()})

                if self.groupBox_show_lines_clusters.isChecked():
                    clasters = self.lfm.sector_to_lines_clusters(points,
                                                max_offset = self.doubleSpinBox_max_offset.value(),
                                                min_cluster_len=self.spinBox_min_cluster_len.value(),
                                                split_threshold=self.doubleSpinBox_split_threshold.value(),
                                                merge_threshold=math.cos(self.doubleSpinBox_merge_threshold.value()/180.*math.pi))

                    if self.checkBox_show_line_cluster_points.isChecked():
                        for i, c in enumerate(clasters):
                            color = QtGui.QColor(QtCore.Qt.GlobalColor(3+i%19)).getRgb()[:-1]
                            primetives.append({"points": c, "color": color, "size": self.spinBox_clasters_size.value()})
                    
                    if self.checkBox_show_line_cluster_lines.isChecked():
                        for i, c in enumerate(clasters):
                            color = QtGui.QColor(QtCore.Qt.GlobalColor(3+i%19)).getRgb()[:-1]
                            primetives.append({"line": {"pos":c[0], "end": c[-1]}, "color": color})
        return primetives

    
    ###########################################################################
    @pyqtSlot(bool)
    def on_toggled(self, state):
        self.settings.beginGroup("lidar_sector")
        self.settings.setValue("show", state)
        self.settings.endGroup()
        
    @pyqtSlot("double")
    def on_doubleSpinBox_start_angle_valueChanged(self, value):
        self.settings.beginGroup("lidar_sector")
        self.settings.setValue("start_angle", value)
        self.settings.endGroup()
        
    @pyqtSlot("double")
    def on_doubleSpinBox_max_radius_valueChanged(self, value):
        self.settings.beginGroup("lidar_sector")
        self.settings.setValue("max_radius", value)
        self.settings.endGroup()

    @pyqtSlot("int")
    def on_spinBox_points_size_valueChanged(self, value):
        self.settings.beginGroup("lidar_sector")
        self.settings.setValue("points_size", value)
        self.settings.endGroup()
        
    @pyqtSlot("bool")
    def on_groupBox_show_points_toggled(self, value):
        self.settings.beginGroup("lidar_sector")
        self.settings.setValue("points", value)
        self.settings.endGroup()
       
    @pyqtSlot(bool)
    def on_groupBox_show_clusters_toggled(self, state):
        self.settings.beginGroup("lidar_sector")
        self.settings.setValue("show_clusters", state)
        self.settings.endGroup()

    @pyqtSlot("int")
    def on_spinBox_clasters_size_valueChanged(self, value):
        self.settings.beginGroup("lidar_sector")
        self.settings.setValue("clasters_size", value)
        self.settings.endGroup()
    
    @pyqtSlot("double")
    def on_doubleSpinBox_max_offset_valueChanged(self, value):
        self.settings.beginGroup("lidar_sector")
        self.settings.setValue("max_offset", value)
        self.settings.endGroup()

    @pyqtSlot("int")
    def on_spinBox_min_cluster_len_valueChanged(self, value):
        self.settings.beginGroup("lidar_sector")
        self.settings.setValue("min_cluster_len", value)
        self.settings.endGroup()
    
    @pyqtSlot(bool)
    def on_checkBox_show_points_clusters_toggled(self, state):
        self.settings.beginGroup("lidar_sector")
        self.settings.setValue("show_points_clusters", state)
        self.settings.endGroup()
   
    @pyqtSlot(bool)
    def on_groupBox_show_lines_clusters_toggled(self, state):
        self.settings.beginGroup("lidar_sector")
        self.settings.setValue("show_lines_clusters", state)
        self.settings.endGroup()
    
    @pyqtSlot("double")
    def on_doubleSpinBox_split_threshold_valueChanged(self, value):
        self.settings.beginGroup("lidar_sector")
        self.settings.setValue("split_threshold", value)
        self.settings.endGroup()

    @pyqtSlot("double")
    def on_doubleSpinBox_merge_threshold_valueChanged(self, value):
        self.settings.beginGroup("lidar_sector")
        self.settings.setValue("merge_threshold", value)
        self.settings.endGroup()
    
    @pyqtSlot(bool)
    def on_checkBox_show_line_cluster_points_toggled(self, state):
        self.settings.beginGroup("lidar_sector")
        self.settings.setValue("show_line_cluster_points", state)
        self.settings.endGroup()
    
    def on_checkBox_show_line_cluster_lines_toggled(self, state):
        self.settings.beginGroup("lidar_sector")
        self.settings.setValue("show_line_cluster_lines", state)
        self.settings.endGroup()
