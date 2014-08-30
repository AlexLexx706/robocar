# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import pyqtSlot, pyqtSignal
import threading
from protocol import Protocol


class MainWindow(QtGui.QMainWindow):
    add_char = pyqtSignal(str)
    add_line = pyqtSignal(str)
    
    KEY_A = 65
    KEY_W = 87
    KEY_D = 68
    KEY_S = 83
    CHECKED_KEYS = [KEY_A, KEY_W, KEY_D, KEY_S]
    
    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)
        uic.loadUi("main_window.ui", self)
        self.settings = QtCore.QSettings("AlexLexx", "car_controlls")
        self.protocol = Protocol()

        self.lineEdit_speed.setText(self.settings.value("speed", "115200").toString())
        self.spinBox_port_name.setValue(self.settings.value("port", 6).toInt()[0])

        
        self.doubleSpinBox_p.setMaximum(self.doubleSpinBox_max_p.value())
        self.doubleSpinBox_i.setMaximum(self.doubleSpinBox_max_i.value())
        self.doubleSpinBox_d.setMaximum(self.doubleSpinBox_max_d.value())
        self.set_angle(self.settings.value("angle", 0).toDouble()[0])
        p = self.settings.value("p", 0).toDouble()[0]
        i = self.settings.value("i", 0).toDouble()[0]
        d = self.settings.value("d", 0).toDouble()[0]
        
        self.doubleSpinBox_max_p.setValue(self.settings.value("max_p", 10).toDouble()[0])
        self.doubleSpinBox_max_i.setValue(self.settings.value("max_i", 10).toDouble()[0])
        self.doubleSpinBox_max_d.setValue(self.settings.value("max_d", 10).toDouble()[0])
        self.set_p(p)
        self.set_i(i)
        self.set_d(d)
        self.set_dt(self.settings.value("dt", 0.01).toDouble()[0])

        self.set_left_wheel_power(self.settings.value("left_wheel_power", 0).toDouble()[0])
        self.set_right_wheel_power(self.settings.value("right_wheel_power", 0).toDouble()[0])
        self.checkBox_enable_key_controll.setCheckState(QtCore.Qt.Checked if self.settings.value("enable_key_controll", False).toBool() else QtCore.Qt.Unchecked)

        self.add_char.connect(self.on_add_char)
        self.add_line.connect(self.on_add_line)
        self.stop_log = False
        self.kay_states = {self.KEY_A: False,
                            self.KEY_W: False,
                            self.KEY_D: False,
                            self.KEY_S: False}
    
    def update_car_controll(self):
        if self.is_enable_key_controll():
            #print self.kay_states
            l = 0.0
            r = 0.0
            max_speed = 0.5
            rotate_koef = 0.8
            
            #вперёд
            if self.kay_states[self.KEY_W]:
                l = max_speed
                r = max_speed
            #назад
            elif self.kay_states[self.KEY_S]:
                l = -max_speed
                r = -max_speed

            #лево
            if self.kay_states[self.KEY_A]:
                if self.kay_states[self.KEY_W]:
                    l = 0
                elif  self.kay_states[self.KEY_S]:
                    l = 0
                else:
                    r = max_speed * rotate_koef
                    l = -max_speed * rotate_koef
            #право
            if self.kay_states[self.KEY_D]:
                if self.kay_states[self.KEY_W]:
                    r = 0
                elif self.kay_states[self.KEY_S]:
                    r = 0
                else:
                    r = -max_speed * rotate_koef
                    l = max_speed * rotate_koef
            
            self.protocol.set_left_wheel_power(l)
            self.protocol.set_right_wheel_power(r)

    def is_enable_key_controll(self):
        return self.checkBox_enable_key_controll.isChecked()
    
    @pyqtSlot(int)
    def on_checkBox_enable_key_controll_stateChanged(self, state):
        self.settings.setValue("enable_key_controll", state == QtCore.Qt.Checked)
        
    @pyqtSlot(int)
    def on_checkBox_enable_debug_stateChanged(self, state):
        self.settings.setValue("enable_debug", state == QtCore.Qt.Checked)
        self.protocol.set_enable_debug(state == QtCore.Qt.Checked)
       
    def winEvent(self, message):
        #wm_keydown
        if message.message == 0x0100:
            if message.wParam in self.CHECKED_KEYS:
                self.kay_states[message.wParam] = True
                self.update_car_controll()
        #wm_keyup
        elif message.message == 0x0101:
            if message.wParam in self.CHECKED_KEYS:
                self.kay_states[message.wParam] = False
                self.update_car_controll()

        return QtGui.QMainWindow.winEvent(self, message)
    
    def on_add_char(self, s):
        cursor = self.plainTextEdit_log.textCursor()
        cursor.movePosition(0, 11)
        cursor.insertText(s)
    
    def on_add_line(self, line):
        self.plainTextEdit_log.appendPlainText(line)
        

    @pyqtSlot()
    def on_pushButton_clear_power_clicked(self):
        self.set_left_wheel_power(0)
        self.set_right_wheel_power(0)

    ###########################################
    @pyqtSlot("int")
    def on_horizontalSlider_left_wheel_valueChanged(self, value):
        self.set_left_wheel_power(-1 + value / float(self.horizontalSlider_left_wheel.maximum()) * 2.0)

    @pyqtSlot("double")
    def on_doubleSpinBox_left_wheel_valueChanged(self, value):
        self.set_left_wheel_power(value)
        
    @pyqtSlot("double")
    def on_doubleSpinBox_dt_valueChanged(self, value):
        self.set_dt(value)

    def set_dt(self, dt):
        self.doubleSpinBox_dt.blockSignals(True)
        self.settings.setValue("dt", dt)
        self.doubleSpinBox_dt.setValue(dt)
        self.doubleSpinBox_dt.blockSignals(False)
        self.send_pid_settings()
    
    def get_dt(self):
        return self.doubleSpinBox_dt.value()
        
    def set_left_wheel_power(self, value):
        self.doubleSpinBox_left_wheel.blockSignals(True)
        self.horizontalSlider_left_wheel.blockSignals(True)

        self.doubleSpinBox_left_wheel.setValue(value)
        self.horizontalSlider_left_wheel.setValue((value + 1.0) / 2.0 * self.horizontalSlider_left_wheel.maximum())

        self.doubleSpinBox_left_wheel.blockSignals(False)
        self.horizontalSlider_left_wheel.blockSignals(False)
        self.settings.setValue("left_wheel_power", value)
        self.protocol.set_left_wheel_power(value)

    def get_left_wheel_power(self):
        return self.doubleSpinBox_left_wheel.value()

    ##########################################################
    @pyqtSlot("int")
    def on_horizontalSlider_right_wheel_valueChanged(self, value):
        self.set_right_wheel_power(-1 + value / float(self.horizontalSlider_right_wheel.maximum()) * 2.0)

    @pyqtSlot("double")
    def on_doubleSpinBox_right_wheel_valueChanged(self, value):
        self.set_right_wheel_power(value)

    def set_right_wheel_power(self, value):
        self.doubleSpinBox_right_wheel.blockSignals(True)
        self.horizontalSlider_right_wheel.blockSignals(True)

        self.doubleSpinBox_right_wheel.setValue(value)
        self.horizontalSlider_right_wheel.setValue((value + 1.0) / 2.0 * self.horizontalSlider_right_wheel.maximum())

        self.doubleSpinBox_right_wheel.blockSignals(False)
        self.horizontalSlider_right_wheel.blockSignals(False)
        self.settings.setValue("right_wheel_power", value)
        self.protocol.set_right_wheel_power(value)

    def get_right_wheel_power(self):
        return self.doubleSpinBox_right_wheel.value()

    ######################################################################
    @pyqtSlot()
    def on_pushButton_send_clicked(self):
        self.protocol.write(str(self.lineEdit_text.text()))
    
    @pyqtSlot("QString")
    def on_lineEdit_speed_textChanged(self, text):
        self.settings.setValue("speed", text)

    @pyqtSlot()
    def on_pushButton_connect_clicked(self):
        if not self.protocol.is_connected():
            speed = int(self.lineEdit_speed.text())

            if self.protocol.connect("COM{}".format(self.spinBox_port_name.value()), speed):
                self.stop_log = False
                self.log_thread = threading.Thread(target=self.log_thread_proc)
                self.log_thread.start()
                self.pushButton_connect.setText(u"Отключить")
        else:
            self.pushButton_connect.setText(u"Подключить")
            self.stop_log = True
            self.log_thread.join()
            self.protocol.close()
    
    def log_thread_proc(self):
        try:
            print "->"
            line = ""
            while not self.stop_log:
                s = self.protocol.read()
                if len(s) > 0:
                    #self.add_char.emit(s)
                    #self.add_line.emit(s)
                    if s != "\n":
                        line += s
                    else:
                        self.add_line.emit(line)
                        line = ""
        finally:
            print "<-"

    @pyqtSlot("int")
    def on_spinBox_port_name_valueChanged(self, value):
        self.settings.setValue("port", value)
            
    @pyqtSlot("int")
    def on_horizontalSlider_p_valueChanged(self, value):
        self.set_p(value / float(self.horizontalSlider_p.maximum()) * self.doubleSpinBox_max_p.value())
    
    @pyqtSlot("double")
    def on_doubleSpinBox_p_valueChanged(self, value):
        self.set_p(value)
    
    @pyqtSlot("double")
    def on_doubleSpinBox_max_p_valueChanged(self, value):
        self.doubleSpinBox_p.setMaximum(value)
        self.settings.setValue("max_p", value)
        
    def get_p(self):
        return self.doubleSpinBox_p.value()
    
    def set_p(self, value):
        self.doubleSpinBox_p.blockSignals(True)
        self.horizontalSlider_p.blockSignals(True)
        self.doubleSpinBox_p.setValue(value)
        self.horizontalSlider_p.setValue(value / self.doubleSpinBox_max_p.value() * self.horizontalSlider_p.maximum())
        self.doubleSpinBox_p.blockSignals(False)
        self.horizontalSlider_p.blockSignals(False)
        self.settings.setValue("p", value)
        self.send_pid_settings()
    
    def send_pid_settings(self):
        self.protocol.set_pid_settings(self.get_p(), self.get_i(), self.get_d(), self.get_dt())

    @pyqtSlot("int")
    def on_horizontalSlider_i_valueChanged(self, value):
        self.set_i(value / float(self.horizontalSlider_i.maximum()) * self.doubleSpinBox_max_i.value())
    
    @pyqtSlot("double")
    def on_doubleSpinBox_i_valueChanged(self, value):
        self.set_i(value)
    
    @pyqtSlot("double")
    def on_doubleSpinBox_max_i_valueChanged(self, value):
        self.doubleSpinBox_i.setMaximum(value)
        self.settings.setValue("max_i", value)
        
    def get_i(self):
        return self.doubleSpinBox_i.value()
    
    def set_i(self, value):
        self.doubleSpinBox_i.blockSignals(True)
        self.horizontalSlider_i.blockSignals(True)
        self.doubleSpinBox_i.setValue(value)
        self.horizontalSlider_i.setValue(value / self.doubleSpinBox_max_i.value() * self.horizontalSlider_i.maximum())
        self.doubleSpinBox_i.blockSignals(False)
        self.horizontalSlider_i.blockSignals(False)
        self.settings.setValue("i", value)
        self.send_pid_settings()
        
        
    @pyqtSlot("int")
    def on_horizontalSlider_d_valueChanged(self, value):
        self.set_d(value / float(self.horizontalSlider_d.maximum()) * self.doubleSpinBox_max_d.value())
    
    @pyqtSlot("double")
    def on_doubleSpinBox_d_valueChanged(self, value):
        self.set_d(value)
    
    @pyqtSlot("double")
    def on_doubleSpinBox_max_d_valueChanged(self, value):
        self.doubleSpinBox_d.setMaximum(value)
        self.settings.setValue("max_d", value)
        
    def get_d(self):
        return self.doubleSpinBox_d.value()
    
    def set_d(self, value):
        self.doubleSpinBox_d.blockSignals(True)
        self.horizontalSlider_d.blockSignals(True)
        self.doubleSpinBox_d.setValue(value)
        self.horizontalSlider_d.setValue(value / self.doubleSpinBox_max_d.value() * self.horizontalSlider_d.maximum())
        self.doubleSpinBox_d.blockSignals(False)
        self.horizontalSlider_d.blockSignals(False)
        self.settings.setValue("d", value)
        self.send_pid_settings()
        
    @pyqtSlot("int")
    def on_dial_angle_valueChanged(self, value):
        value = value / float(self.dial_angle.maximum())
        self.set_angle(self.doubleSpinBox_angle.minimum() + (self.doubleSpinBox_angle.maximum() - self.doubleSpinBox_angle.minimum()) * value)
    
    @pyqtSlot("double")
    def on_doubleSpinBox_angle_valueChanged(self, value):
        self.set_angle(value)
    
    def get_angle(self):
        return self.doubleSpinBox_angle.value()
        
    def set_angle(self, angle):
        self.doubleSpinBox_angle.blockSignals(True)
        self.dial_angle.blockSignals(True)

        self.doubleSpinBox_angle.setValue(angle)
        value = (self.doubleSpinBox_angle.value() - self.doubleSpinBox_angle.minimum()) / (self.doubleSpinBox_angle.maximum() - self.doubleSpinBox_angle.minimum())
        self.dial_angle.setValue(self.dial_angle.maximum() * value)
        
        self.doubleSpinBox_angle.blockSignals(False)
        self.dial_angle.blockSignals(False)
        
        self.settings.setValue("angle", angle)
        self.protocol.set_angle(angle)