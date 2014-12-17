# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import pyqtSlot, pyqtSignal
from car_control import set_direction_move
import threading
import time

class AlgControls(QtGui.QFrame):
    def __init__(self, settings, protocol):
        super(QtGui.QFrame, self).__init__()
        uic.loadUi("alg_controls.ui", self)
        self.settings = settings
        self.protocol = protocol
        self.init_controls()
        self.lock = threading.Lock()
        self.angle = None
        self.stop_flag = True
    
    def update_angle(self, angle):
        with self.lock:
            self.angle = angle
    
    def get_angle(self):
        with self.lock:
            res = self.angle
            self.angle = None
            return res
    
    def start(self):
        print "start"
        if self.stop_flag:
            if not self.protocol.is_connected():
                return

            self.stop_flag = False
            self.control_thread = threading.Thread(target=self.control_proc)
            self.pushButton_start.setText(u"Стоп")
            self.control_thread.start()

    def stop(self):
        print "stop"
        if not self.stop_flag:
            self.stop_flag = True
            self.control_thread.join()
            self.pushButton_start.setText(u"Старт")

    @pyqtSlot('bool')
    def on_pushButton_start_clicked(self, v):
        if not self.stop_flag:
            self.stop()
        else:
            self.start()

    
    def control_proc(self):
        while not self.stop_flag:
            angle = self.get_angle()
            print "!!!!!!!!angle:", angle
            #dвызов управления
            if angle is not None:

                set_direction_move(self.protocol,
                                angle,
                                async=True,
                                motion_p=self.doubleSpinBox_MOTION_SPEED_P.value(),
                                min_speed=self.doubleSpinBox_MIN_SPEED.value(),
                                max_speed=self.doubleSpinBox_MAX_SPEED.value(),
                                min_turn_angle=self.doubleSpinBox_MIN_TURN_ANGLE.value(),
                                turn_p=self.doubleSpinBox_turn_p.value())

            time.sleep(self.doubleSpinBox_period.value())
        self.protocol.set_power_zerro()

    @pyqtSlot("double")
    def on_doubleSpinBox_period_valueChanged(self, value):
        self.settings.beginGroup("alg")
        self.settings.setValue("period", value)
        self.settings.endGroup()

    @pyqtSlot("double")
    def on_doubleSpinBox_MOTION_SPEED_P_valueChanged(self, value):
        self.settings.beginGroup("alg")
        self.settings.setValue("MOTION_SPEED_P", value)
        self.settings.endGroup()

    @pyqtSlot("double")
    def on_doubleSpinBox_MIN_SPEED_valueChanged(self, value):
        self.settings.beginGroup("alg")
        self.settings.setValue("MIN_SPEED", value)
        self.settings.endGroup()

    @pyqtSlot("double")
    def on_doubleSpinBox_MAX_SPEED_valueChanged(self, value):
        self.settings.beginGroup("alg")
        self.settings.setValue("MAX_SPEED", value)
        self.settings.endGroup()
        
    @pyqtSlot("double")
    def on_doubleSpinBox_MIN_TURN_ANGLE_valueChanged(self, value):
        self.settings.beginGroup("alg")
        self.settings.setValue("MIN_TURN_ANGLE", value)
        self.settings.endGroup()
    
    @pyqtSlot("double")
    def on_doubleSpinBox_turn_p_valueChanged(self, value):
        self.settings.beginGroup("alg")
        self.settings.setValue("turn_p", value)
        self.settings.endGroup()
    

    def init_controls(self):
        self.doubleSpinBox_period.blockSignals(True)
        self.doubleSpinBox_MOTION_SPEED_P.blockSignals(True)
        self.doubleSpinBox_MIN_SPEED.blockSignals(True)
        self.doubleSpinBox_MAX_SPEED.blockSignals(True)
        self.doubleSpinBox_MIN_TURN_ANGLE.blockSignals(True)
        self.doubleSpinBox_turn_p.blockSignals(True)

        self.settings.beginGroup("alg")
        self.doubleSpinBox_period.setValue(self.settings.value("period", 0.2).toDouble()[0])
        self.doubleSpinBox_MOTION_SPEED_P.setValue(self.settings.value("MOTION_SPEED_P", 0.06).toDouble()[0])
        self.doubleSpinBox_MIN_SPEED.setValue(self.settings.value("MIN_SPEED", 0.4).toDouble()[0])
        self.doubleSpinBox_MAX_SPEED.setValue(self.settings.value("MAX_SPEED", 0.8).toDouble()[0])
        self.doubleSpinBox_MIN_TURN_ANGLE.setValue(self.settings.value("MIN_TURN_ANGLE", 0.08).toDouble()[0])
        self.doubleSpinBox_turn_p.setValue(self.settings.value("turn_p", 1.12).toDouble()[0])
        self.settings.endGroup()

        self.doubleSpinBox_period.blockSignals(False)
        self.doubleSpinBox_MOTION_SPEED_P.blockSignals(False)
        self.doubleSpinBox_MIN_SPEED.blockSignals(False)
        self.doubleSpinBox_MAX_SPEED.blockSignals(False)
        self.doubleSpinBox_MIN_TURN_ANGLE.blockSignals(False)
        self.doubleSpinBox_turn_p.blockSignals(False)

if __name__ == '__main__':
    import logging
    import sys
    #logging.basicConfig(format='%(levelname)s %(name)s::%(funcName)s%(message)s', level=logging.INFO)
    #logging.getLogger("PyQt4").setLevel(logging.INFO)
    
    app = QtGui.QApplication(sys.argv)
    class xxx:
        def is_connected(self):
            return False
            
    widget = AlgControls(QtCore.QSettings("AlexLexx", "car_controlls"), xxx())
    app.installEventFilter(widget)
    widget.show()
    sys.exit(app.exec_())
        