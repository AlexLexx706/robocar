# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import pyqtSlot, pyqtSignal
import threading
from protocol import Protocol
from cross_detector.ffmpeg_reader import FFmpegReader

class MainWindow(QtGui.QMainWindow):
    new_frame = pyqtSignal("QImage")
    
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

        self.set_angle(self.settings.value("angle", 0).toDouble()[0])
       
        self.set_p(self.settings.value("p", 2).toDouble()[0])
        self.set_i(self.settings.value("i", 0).toDouble()[0])
        self.set_d(self.settings.value("d", 0.3).toDouble()[0])
        
        self.set_offset(self.settings.value("offset", 0).toDouble()[0])

        self.set_left_wheel_power(self.settings.value("left_wheel_power", 0).toDouble()[0])
        self.set_right_wheel_power(self.settings.value("right_wheel_power", 0).toDouble()[0])
        self.checkBox_enable_key_controll.setCheckState(QtCore.Qt.Checked if self.settings.value("enable_key_controll", False).toBool() else QtCore.Qt.Unchecked)

        #self.add_char.connect(self.on_add_char)
        self.protocol.add_line.connect(self.on_add_line)
        self.protocol.update_info.connect(self.on_update_info)
        
        self.kay_states = {self.KEY_A: False,
                            self.KEY_W: False,
                            self.KEY_D: False,
                            self.KEY_S: False}
        
        self.new_frame.connect(self.on_new_frame)
        threading.Thread(target=self.read_frame).start()
        
        #подключим управление камерой через мышку
        self.label_video.start_move_camera.connect(self.on_start_move_camera)
        self.label_video.move_camera.connect(self.on_move_camera)
        self.camera_start_pos = None
        self.label_video.addAction(self.action_reset_camera)
        self.plainTextEdit_log.addAction(self.action_clear)
    
    def on_update_info(self, data):
        self.label_giro_x.setText("{:10.4f}".format(data[0]))
        self.label_giro_y.setText("{:10.4f}".format(data[1]))
        self.label_giro_z.setText("{:10.4f}".format(data[2]))
        

        self.label_acel_x.setText("{:10.4f}".format(data[3]))
        self.label_acel_y.setText("{:10.4f}".format(data[4]))
        self.label_acel_z.setText("{:10.4f}".format(data[5]))


        self.label_distance.setText(str(data[6]))
        
        self.label_left_speed.setText(str(data[7]))
        self.label_right_speed.setText(str(data[8]))

        self.label_left_count.setText(str(data[9]))
        self.label_right_count.setText(str(data[10]))

        self.label_servo_1.setText(str(data[11]))
        self.label_servo_2.setText(str(data[12]))
    
    @pyqtSlot(bool)
    def on_groupBox_update_state_toggled(self, state):
        if not state:
            self.protocol.set_info_period(0xffffffff)
        else:
            self.protocol.set_info_period(self.spinBox_info_period.value())
    
    @pyqtSlot(bool)
    def on_action_reset_camera_triggered(self, v):
        self.set_servo_1_angle(98)
        self.set_servo_2_angle(68)
    
    def on_start_move_camera(self, pos):
        self.camera_start_pos = [self.get_servo_1_angle(), self.get_servo_2_angle()]

    def on_move_camera(self, pos):
        k = 0.5
        self.set_servo_1_angle(self.camera_start_pos[0] - int(pos.x() * k))
        self.set_servo_2_angle(self.camera_start_pos[1] - int(pos.y() * k))


        
    def read_frame(self):
        reader = FFmpegReader()
        reader.process_direct_show_video()
        
        while 1:
            image = QtGui.QImage(reader.read_string(), reader.size[0], reader.size[1], reader.size[0] * 3, QtGui.QImage.Format_RGB888)
            self.new_frame.emit(image)
    
    def on_new_frame(self, image):
        self.label_video.setPixmap(QtGui.QPixmap.fromImage(image))
    
    
    def update_car_controll(self):
        if self.is_enable_key_controll():
            #print self.kay_states
            l = 0.0
            r = 0.0
            max_speed = 0.7
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
    
    @pyqtSlot(bool)
    def on_action_clear_triggered(self, v):
        self.plainTextEdit_log.clear()

    ###########################################
    @pyqtSlot("int")
    def on_horizontalSlider_left_wheel_valueChanged(self, value):
        self.set_left_wheel_power(-1 + value / float(self.horizontalSlider_left_wheel.maximum()) * 2.0)

    @pyqtSlot("double")
    def on_doubleSpinBox_left_wheel_valueChanged(self, value):
        self.set_left_wheel_power(value)

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
    def on_lineEdit_text_editingFinished(self):
        self.protocol.write(str(self.lineEdit_text.text()))
        self.lineEdit_text.setText("")
    
    @pyqtSlot("QString")
    def on_lineEdit_speed_textChanged(self, text):
        self.settings.setValue("speed", text)

    @pyqtSlot()
    def on_pushButton_connect_clicked(self):
        if not self.protocol.is_connected():
            speed = int(self.lineEdit_speed.text())

            if self.protocol.connect("COM{}".format(self.spinBox_port_name.value()), speed):
                self.pushButton_connect.setText(u"Отключить")
        else:
            self.pushButton_connect.setText(u"Подключить")
            self.protocol.close()
    
    @pyqtSlot("int")
    def on_spinBox_port_name_valueChanged(self, value):
        self.settings.setValue("port", value)
    
    def get_value(self, slider, spin_box):
        return slider.value() / float(slider.maximum()) * (spin_box.maximum() - spin_box.minimum()) + spin_box.minimum()
    
    def set_value(self, slider, spin_box, value):
        spin_box.blockSignals(True)
        slider.blockSignals(True)
        spin_box.setValue(value)
        slider.setValue((value - spin_box.minimum()) / (spin_box.maximum() - spin_box.minimum()) * slider.maximum())
        spin_box.blockSignals(False)
        slider.blockSignals(False)

        
    def get_pid_type(self):
        if self.radioButton_angle.isChecked():
            return 0
            
        if self.radioButton_left_wheel.isChecked():
            return 1
        
        if self.radioButton_right_wheel.isChecked():
            return 2
        
    def set_pid_type(self, pid_type):
        if pid_type == 0:
            self.radioButton_angle.setChecked(True)
        elif pid_type == 1:
            self.radioButton_left_wheel.setChecked(True)
        elif pid_type == 2:
            self.radioButton_right_wheel.setChecked(True)

        
    @pyqtSlot("int")
    def on_horizontalSlider_p_valueChanged(self, value):
        self.set_p(self.get_value(self.horizontalSlider_p, self.doubleSpinBox_p))
    
    @pyqtSlot("double")
    def on_doubleSpinBox_p_valueChanged(self, value):
        self.set_p(value)
        
    def get_p(self):
        return self.doubleSpinBox_p.value()
    
    def set_p(self, value):
        self.set_value(self.horizontalSlider_p, self.doubleSpinBox_p, value)
        self.settings.setValue("p", value)
        self.send_pid_settings()
    
    def send_pid_settings(self):
        self.protocol.set_pid_settings(self.get_pid_type(), self.get_p(), self.get_i(), self.get_d())

    @pyqtSlot("int")
    def on_horizontalSlider_i_valueChanged(self, value):
        self.set_i(self.get_value(self.horizontalSlider_i, self.doubleSpinBox_i))
    
    @pyqtSlot("double")
    def on_doubleSpinBox_i_valueChanged(self, value):
        self.set_i(value)
        
    def get_i(self):
        return self.doubleSpinBox_i.value()
    
    def set_i(self, value):
        self.set_value(self.horizontalSlider_i, self.doubleSpinBox_i, value)
        self.settings.setValue("i", value)
        self.send_pid_settings()
        
    @pyqtSlot("int")
    def on_horizontalSlider_d_valueChanged(self, value):
        self.set_d(self.get_value(self.horizontalSlider_d, self.doubleSpinBox_d))
    
    @pyqtSlot("double")
    def on_doubleSpinBox_d_valueChanged(self, value):
        self.set_d(value)

    def get_d(self):
        return self.doubleSpinBox_d.value()
    
    def set_d(self, value):
        self.set_value(self.horizontalSlider_d, self.doubleSpinBox_d, value)
        self.settings.setValue("d", value)
        self.send_pid_settings()
    
    @pyqtSlot("int")
    def on_horizontalSlider_offset_valueChanged(self, value):
        self.set_offset(value/float(self.horizontalSlider_offset.maximum()) * 2 - 1.0);

    @pyqtSlot("double")
    def on_doubleSpinBox_offset_valueChanged(self, value):
        self.set_offset(value)
    
    def set_offset(self, value):
        self.horizontalSlider_offset.blockSignals(True)
        self.doubleSpinBox_offset.blockSignals(True)
        self.horizontalSlider_offset.setValue((value + 1)/2. * self.horizontalSlider_offset.maximum())
        self.doubleSpinBox_offset.setValue(value)
        self.doubleSpinBox_offset.blockSignals(False)
        self.horizontalSlider_offset.blockSignals(False)
        self.settings.setValue("offset", value)
        self.protocol.set_offset(value)
    
    def get_offset(self):
        return self.doubleSpinBox_offset.value()
    
    @pyqtSlot()
    def on_pushButton_stop_clicked(self):
        self.set_offset(0)
        self.set_left_wheel_power(0)
        self.set_right_wheel_power(0)
        
    @pyqtSlot()
    def on_pushButton_start_walk_clicked(self):
        self.protocol.start_walk()
    
    @pyqtSlot("int")
    def on_dial_angle_valueChanged(self, value):
        value = value / float(self.dial_angle.maximum())
        self.set_angle(self.doubleSpinBox_angle.minimum() + (self.doubleSpinBox_angle.maximum() - self.doubleSpinBox_angle.minimum()) * value)
    
    @pyqtSlot("double")
    def on_doubleSpinBox_angle_valueChanged(self, value):
        self.set_angle(value)
    
    @pyqtSlot("int")
    def on_spinBox_servo_1_valueChanged(self, value):
        self.protocol.set_servo_angle(0, value)
    
    def get_servo_1_angle(self):
        return self.spinBox_servo_1.value()

    def set_servo_1_angle(self, angle):
        self.spinBox_servo_1.setValue(angle)

    def get_servo_2_angle(self):
        return self.spinBox_servo_2.value()

    def set_servo_2_angle(self, angle):
        self.spinBox_servo_2.setValue(angle)


    @pyqtSlot("int")
    def on_spinBox_servo_2_valueChanged(self, value):
        self.protocol.set_servo_angle(1, value)

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
    
    def get_wheel_id(self):
        if self.radioButton_left_wheel_speed.isChecked():
            return 0
        elif self.radioButton_right_wheel_speed.isChecked():
            return 1
        return 2
    
    @pyqtSlot("int")
    def on_horizontalSlider_speed_valueChanged(self, value):
        self.protocol.set_wheel_speed(self.get_wheel_id(), value)