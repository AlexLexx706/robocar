# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import pyqtSlot, pyqtSignal
import threading
from car_controll.protocol import Protocol
import pyqtgraph as pg
import numpy as np
import math
from robot_scene import RobotScene
from robot_scene import RobotScene
from LidarFrame import LidarFrame
import Queue

class MainWindow(QtGui.QMainWindow):
    KEY_A = 65
    KEY_W = 87
    KEY_D = 68
    KEY_S = 83
    CHECKED_KEYS = [KEY_A, KEY_W, KEY_D, KEY_S]
    add_line = pyqtSignal(str)
    update_info = pyqtSignal(object)
    
    
    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)
        uic.loadUi("main_window.ui", self)
        self.settings = QtCore.QSettings("AlexLexx", "car_controlls")
        
        self.read_protocol_res_thread = threading.Thread(target=self.read_protocol_res)
        self.protocol_result_queue = Queue.Queue()
        self.read_protocol_res_thread.start()

        self.protocol = Protocol(self.protocol_result_queue)

        self.lineEdit_speed.setText(self.settings.value("speed", "115200").toString())
        self.spinBox_port_name.setValue(self.settings.value("port", 6).toInt()[0])

        self.set_angle(self.settings.value("angle", 0).toDouble()[0])
       
        self.set_p(self.settings.value("p", 2).toDouble()[0])
        self.set_i(self.settings.value("i", 0).toDouble()[0])
        self.set_d(self.settings.value("d", 0.3).toDouble()[0])
        
        self.set_offset(self.settings.value("offset", 0).toDouble()[0])

        self.set_left_wheel_power(self.settings.value("left_wheel_power", 0).toDouble()[0])
        self.set_right_wheel_power(self.settings.value("right_wheel_power", 0).toDouble()[0])
        self.checkBox_enable_key_controll.setCheckState(QtCore.Qt.Checked if self.settings.value("enable_key_controll", True).toBool()
            else QtCore.Qt.Unchecked)

        self.spinBox_socket_port.setValue(self.settings.value("socket_port", 1111).toInt()[0])
        self.lineEdit_socket_host.setText(self.settings.value("socket_host", "192.168.0.91").toString())
        self.set_connection_type(self.settings.value("connection_type", 0).toInt()[0])

        #self.add_char.connect(self.on_add_char)
        self.add_line.connect(self.on_add_line)
        self.update_info.connect(self.on_update_info)
        
        self.kay_states = {self.KEY_A: False,
                            self.KEY_W: False,
                            self.KEY_D: False,
                            self.KEY_S: False}
        
        #подключим управление камерой через мышку
        self.camera_start_pos = None
        self.plainTextEdit_log.addAction(self.action_clear)
        
        #Добавим графики
        self.win = pg.GraphicsWindow()
        self.verticalLayout_10.addWidget(self.win)

        self.cur_plot = self.win.addPlot(title="Updating plot")
        self.curves = [self.cur_plot.plot(pen=(255,0,0)),
                       self.cur_plot.plot(pen=(0,255,0)),
                       self.cur_plot.plot(pen=(0,0,255))]

        #self.data = np.random.normal(size=(10,1000))
        self.data_list = [[0.0 for i in range(1000)], [0 for i in range(1000)], [0 for i in range(1000)]]
        self.first = True
        
        self.scene = RobotScene()
        self.graphicsView.setScene(self.scene)
        self.graphicsView.addAction(self.action_clear_map)

        self.wheel_timer = QtCore.QTimer()
        self.wheel_timer.timeout.connect(self.on_update_wheels)
        self.wheel_timer.setInterval(100)
        self.wheel_timer.setSingleShot(False)
        self.l = 0.0
        self.r = 0.0
        self.use_giro_control = True
        
        #добавим лидар
        self.lidar_frame = LidarFrame(self.settings, self)
        self.tabWidget_2.addTab(self.lidar_frame, u"Лидар")
        self.lidar_frame.label_video.start_move_camera.connect(self.on_start_move_camera)
        self.lidar_frame.label_video.move_camera.connect(self.on_move_camera)
        self.lidar_frame.label_video.addAction(self.action_reset_camera)

    def read_protocol_res(self):
        while 1:
            data = self.protocol_result_queue.get()
            #текст
            if data[0] == 0:
                self.add_line.emit(data[1])
            elif data[0] == 1:
                self.update_info.emit(data[1])

    def get_connection_type(self):
        return 0 if self.radioButton_com.isChecked() else 1
    
    def set_connection_type(self, t):
        if t == 0:
            self.radioButton_com.setChecked(True)
        else:
            self.radioButton_socket.setChecked(True)

        self.settings.setValue("connection_type", t)
    
    @pyqtSlot(bool)
    def on_action_clear_map_triggered(self, v):
        self.scene.clear_map()
    
    @pyqtSlot(int)
    def on_checkBox_folow_robot_stateChanged(self, state):
        self.scene.set_follow_robot(QtCore.Qt.Checked == state)
    
    def update(self, data):
        K  = 0.05
        self.data_list[0] = self.data_list[0][1:]
        self.data_list[0].append((1.0 - K) * self.data_list[0][-1] + K * data[0])
        self.curves[0].setData(self.data_list[0])

        self.data_list[1] = self.data_list[1][1:]
        self.data_list[1].append((1.0 - K) * self.data_list[1][-1] + K * data[1])
        self.curves[1].setData(self.data_list[1])

        v = self.data_list[0][-1] / math.cos(math.atan(self.data_list[1][-1] / self.data_list[0][-1]))
        
        self.data_list[2] = self.data_list[2][1:]
        self.data_list[2].append(v)
        self.curves[2].setData(self.data_list[2])
        
        
        #
        #for i, v in enumerate(data):
        #    self.data_list[i] = self.data_list[i][1:]
        #    
        #    #применим фильтр низкой частоты
        #    v = (1 - K) * self.data_list[i][-1] + K * v
        #    self.data_list[i].append(v)
        #    self.curves[i].setData(self.data_list[i])

        if self.first:
            self.cur_plot.enableAutoRange('xy', False)  ## stop auto-scaling after the first data set is plotted
            self.first = False
        
    
    def on_update_info(self, data):
        self.update(data[3:6])
        self.label_giro_x.setText("{:10.4f}".format(data[0]))
        self.label_giro_y.setText("{:10.4f}".format(data[1]))
        self.label_giro_z.setText("{:10.4f}".format(data[2]))
        

        self.label_acel_x.setText("{:10}".format(data[3]))
        self.label_acel_y.setText("{:10}".format(data[4]))
        self.label_acel_z.setText("{:10}".format(data[5]))
        self.label_distance.setText("{:10.4f}".format(data[6]))
        
        self.label_left_speed.setText(str(data[7]))
        self.label_right_speed.setText(str(data[8]))

        self.label_left_count.setText(str(data[9]))
        self.label_right_count.setText(str(data[10]))
        self.scene.update_wheel_count(data[9], data[10], data[0])

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
        self.set_servo_2_angle(self.camera_start_pos[0] - int(pos.x() * k))
        self.set_servo_1_angle(self.camera_start_pos[1] - int(pos.y() * k))
   
    def update_car_controll(self):
        if self.is_enable_key_controll():
            #используем гиро контроль
            if not self.use_giro_control:
                self.on_update_wheels_2()
                self.wheel_timer.stop()

                if self.kay_states[self.KEY_A] or self.kay_states[self.KEY_D]:
                    self.wheel_timer.start()
            else:
                #print self.kay_states
                self.l = 0.0
                self.r = 0.0
                max_speed = 0.6
                rotate_koef = 0.6
                
                #вперёд
                if self.kay_states[self.KEY_W]:
                    self.l = max_speed
                    self.r = max_speed
                #назад
                elif self.kay_states[self.KEY_S]:
                    self.l = -max_speed
                    self.r = -max_speed

                #лево
                if self.kay_states[self.KEY_A]:
                    if self.kay_states[self.KEY_W]:
                        self.l = 0
                    elif  self.kay_states[self.KEY_S]:
                        self.l = 0
                    else:
                        self.r = max_speed * rotate_koef
                        self.l = -max_speed * rotate_koef
                #право
                if self.kay_states[self.KEY_D]:
                    if self.kay_states[self.KEY_W]:
                        self.r = 0
                    elif self.kay_states[self.KEY_S]:
                        self.r = 0
                    else:
                        self.r = -max_speed * rotate_koef
                        self.l = max_speed * rotate_koef

                self.on_update_wheels()
                self.wheel_timer.stop()

                if self.r != 0 or self.l != 0:
                    self.wheel_timer.start()

       
    def on_update_wheels(self):
        if not self.use_giro_control:
            self.protocol.set_left_wheel_power(self.l)
            self.protocol.set_right_wheel_power(self.r)
        #используем гиро контроль
        else:
            angle = math.pi/180. * 20
            angle_speed=math.pi/ 180. * 80.
            power = 0.6
            
            if self.kay_states[self.KEY_A]:
                self.protocol.turn(angle, angle_speed=angle_speed)
                        
            elif self.kay_states[self.KEY_D]:
                self.protocol.turn(-angle, angle_speed=angle_speed)

            if self.kay_states[self.KEY_W]:
                self.protocol.set_offset(power)
            elif self.kay_states[self.KEY_S]:
                self.protocol.set_offset(-power)
            else:
                self.protocol.set_offset(0)        

      
        
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
                if not self.kay_states[message.wParam]:
                    self.kay_states[message.wParam] = True
                    self.update_car_controll()
        #wm_keyup
        elif message.message == 0x0101:
            if message.wParam in self.CHECKED_KEYS:
                if self.kay_states[message.wParam]:
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

            #COM port
            if self.get_connection_type() == 0:
                settings = {"port": "COM{}".format(self.spinBox_port_name.value()),
                            "baudrate": int(self.lineEdit_speed.text()),
                            "timeout": 2,
                            "writeTimeout": 2}
                
                if self.protocol.connect(0, settings):
                    self.pushButton_connect.setText(u"Отключить")
            #socket
            else:
                settings = {"host": unicode(self.lineEdit_socket_host.text()),
                            "port": self.spinBox_socket_port.value()}
                
                if self.protocol.connect(1, settings):
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

        self.protocol.turn(angle)
    
    def get_wheel_id(self):
        if self.radioButton_left_wheel_speed.isChecked():
            return 0
        elif self.radioButton_right_wheel_speed.isChecked():
            return 1
        return 2


    @pyqtSlot("int")
    def on_horizontalSlider_speed_valueChanged(self, value):
        self.protocol.set_wheel_speed(self.get_wheel_id(), value)

    @pyqtSlot(bool)
    def on_radioButton_com_toggled(self, v):
        if v:
            self.set_connection_type(0)
        else:
            self.set_connection_type(1)

    @pyqtSlot(bool)
    def on_radioButton_socket_toggled(self, v):
        if v:
            self.set_connection_type(1)
        else:
            self.set_connection_type(0)
        
    @pyqtSlot(int)
    def on_spinBox_socket_port_valueChanged(self, value):
        self.settings.setValue("socket_port", value)

    @pyqtSlot("QString")
    def on_lineEdit_socket_host_textChanged(self, text):
        self.settings.setValue("socket_host", text)