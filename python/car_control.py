#!/usr/bin/python
# coding: utf-8

print 'Script begin'

# Система управления
import sys, time, collections as coll, pdb

from math import sin, cos, pi, radians#, copysign
import random as rnd
#import numpy as np

from tcp_rpc.client import Client as SensorsClient
from car_controll.protocol import Protocol

import right_wall_lidar_motion as rwlm

import loggers
import procUtils as pu
from launcher import getTxtArgsCmd
import os

print 'Script imports passed'

PROFILE = False
#PROFILE = True

EMULATE_SENSORS = True
EMULATE_SENSORS = False

CONTROL_MOVE_DIR = True
#CONTROL_MOVE_DIR = False

STOP_BEFORE_TURN = True
STOP_BEFORE_TURN = False

VISUALIZE_LIDAR = True
#VISUALIZE_LIDAR = False

USE_LOCAL_LIDAR = False
#USE_LOCAL_LIDAR = True

EMULATE_MAV = True
#EMULATE_MAV = False

ARM_MOTORS = False

#THREAD_LIDAR_PROCESSING = False
#THREAD_LIDAR_PROCESSING = True

USE_MATPLOTLIB = True
USE_MATPLOTLIB = False

STABLE_THROTTLE = 1483
STABLE_PITCH = 1488
STABLE_ROLL = 1485
STABLE_YAW = 1491

MAX_SENSOR_PITCH = .5 # Max pitch in rad
MAX_SENSOR_ROLL = .5 # Max roll in rad

Malt = .25
ALT_BOUNDS = .01

Pthrottle = 10.
Pyaw = -5.
Ppitch = 10.
Proll = -10.

DEFAULT_WALL_ROUNDING_ANGLE_STEP = pi/8
MIN_SPEED = .4
MAX_SPEED = .8

MIN_TURN_ANGLE = pi/36
MAIN_CYCLE_SLEEP = .2
#WALL_ROUNDING_ANGLE = DEFAULT_WALL_ROUNDING_ANGLE_STEP

TURN_SPEED_P = 1.12
MOTION_SPEED_P = .06

ASYNC_TURNS = False
ASYNC_TURNS = True 


CONTROL_STATE = 'control'

#import matplotlib as mpl
#import matplotlib.pyplot as plt
#import matplotlib.animation as animation
#from matplotlib.collections import PatchCollection
#from matplotlib.patches import Polygon, FancyBboxPatch, BoxStyle, Rectangle, FancyArrowPatch

#from pymavlink import mavlinkv10 as mavlink
if not EMULATE_MAV:
	import pymavlink.dialects.v10.ardupilotmega as mavlink
	from pymavlink import mavutil

FIG_SIZE = (16,9)
BOX_WIDTH, BOX_HEIGHT = (80, 40)
BARRIER_THICK = .1
MAX_MEASURE_DISTANCE = 5
ORT = pi/2

COPTER_START_POS = (40, 20)
WALLS = {}
HALF_WALL_LEN = 1
#WALLS_DIST = {}
WALLS_BUF = []
WALL_COLLECTION = None
STATUS_X = {0: 1, -ORT: 10}
STATUS_TEXT = {0: 'Front wall: %1.2f', -ORT: 'Right wall: %1.2f'}
STATUS_OBJECTS = {}

ALT_CONTROL = 'Alt control'

CONTROL_IMPULSE_TIME = .2

def offset_angle_to_control(a):
	return rwlm.normalize_angle(a-Af)

def set_status(x, text):
	if not USE_MATPLOTLIB:
		return

	obj = STATUS_OBJECTS.get(x, None)
	if obj:
		obj.remove()

	STATUS_OBJECTS[x] = ax.text(x, 3, text, size=10, ha="left", va="center")


def measure_distance(x, y, a):

	if not EMULATE_SENSORS:
		res = s.us_get_distance() if a==0 else s.ik_get_distance()
		res /= 100
	else:
		res = rnd.uniform(5, 100)

	A = a+Af
	MIDDLE = [x+res*cos(A), y+res*sin(A)]
	WALLS[a] = ((MIDDLE[0]+HALF_WALL_LEN*cos(A-ORT), MIDDLE[1]+HALF_WALL_LEN*sin(A-ORT)), (MIDDLE[0]+HALF_WALL_LEN*cos(A+ORT),
				MIDDLE[1]+HALF_WALL_LEN*sin(A+ORT)))
#	print 'Angle:', a, ', Measured distance:', res#, 'wall:', WALLS[a]
	set_status(STATUS_X[a], STATUS_TEXT[a]%res)
	return res


NOP = 65535
CONTROL_MODE = 0
#INTERRUPT_CONTROL_MODE = 2 # 0

STATES = coll.OrderedDict()
COPTER_CONTROL_STATE = 'copter_control'

ANGLE_CONTROL_THRSH = pi/36
HEIGHT_CONTROL_THRSH = .1

# Интерфейс управления коптером
def control_copter(pitch=NOP, roll=NOP, throttle=NOP, yaw=NOP):
		channels = [ pitch, roll, throttle, yaw ]
		channels.extend([ 0 ] * 4)
#		 print 'System:', system, 'target component: ', target_component
#		 print 'master system:', master.target_system, 'master target component: ', master.target_component
		if check_return_rc_control():
			return

		if master.messages['HEARTBEAT'].custom_mode != INTERRUPT_CONTROL_MODE:
				STATES[COPTER_CONTROL_STATE] = 'Controlling copter...'
				mav.rc_channels_override_send(master.target_system, master.target_component, *channels)

#		 master.recv_match(type='ACTION_ACK', blocking=True)
#		 mav.rc_channels_override_send(system, target_component, *([ 0 ]*8))

def proportional_control(sensor_value, desired_value, P, stable_pwm):
	pwm = int((1+(desired_value-sensor_value)*P)*stable_pwm)
	assert 1000<pwm<2000, 'PWM %d is out of range!'%pwm
	return pwm

def move(protocol, angle, p=MOTION_SPEED_P, min_speed=MIN_SPEED, max_speed=MAX_SPEED, min_turn_angle=MIN_TURN_ANGLE):
		return set_car_motion_speed(protocol, angle)

		global step, x_delta, y_delta
		
		Dx = step*cos(a)
		Dy = step*sin(a)
		
#		print 'Move copter! Dx:', Dx, 'Dy:', Dy, 'angle:', a
#		raw_input('Press Enter...')
		
		new_x = x+Dx
		new_y = y+Dy

		impulse_pitch = proportional_control(cos(Af), cos(a), Ppitch, STABLE_PITCH)
#		impulse_pitch = (1+cos(a)*Mpitch)*STABLE_PITCH # вычислять пропорциональный импульс

		impulse_roll = proportional_control(sin(Af), sin(a), Proll, STABLE_ROLL)
#		impulse_roll = (1-sin(a)*Mroll)*STABLE_ROLL # вычислять пропорциональный импульс

		STATES['pitch_roll'] = 'pitch: %d roll: %d'%(impulse_pitch, impulse_roll)

#		print 'impulse_roll:', impulse_roll, 'impulse_pitch:', impulse_pitch
		if CONTROL_MOVE_DIR and not EMULATE_MAV:
			control_copter(pitch=impulse_pitch, roll=impulse_roll)
			time.sleep(CONTROL_IMPULSE_TIME)
			control_copter(pitch=STABLE_PITCH, roll=STABLE_ROLL)
		
		return new_x, new_y


def set_alt(x, y, alt):
		return
		global Alt
#		print 'Move copter! Dx:', Dx, 'Dy:', Dy, 'angle:', a
#		raw_input('Press Enter...')
		
		alt_error = abs(Alt-alt)
		STATES[ALT_CONTROL] = "Alt: %.2f Alt error: %.2f"%(Alt, alt_error)
		if alt_error < ALT_BOUNDS:
			STATES[ALT_CONTROL] = "Alt: %.2f in allowed bounds %.2f around %.2f"%(Alt, ALT_BOUNDS, alt)
			control_copter(throttle=STABLE_THROTTLE)
			return

		impulse_throttle = proportional_control(Alt, alt, Pthrottle, STABLE_THROTTLE)
#(1+sign(alt-Alt)*Mthrottle)*STABLE_THROTTLE # вычислять пропорциональный импульс
#		impulse_throttle = (1+sign(alt-Alt)*Mthrottle)*STABLE_THROTTLE # вычислять пропорциональный импульс

		STATES[ALT_CONTROL] += " Throttle: %d"%impulse_throttle
		if not EMULATE_MAV:
				control_copter(throttle=impulse_throttle)
#				time.sleep(CONTROL_IMPULSE_TIME)
#				control_copter(throttle=STABLE_THROTTLE)


def turn_to(protocol, a, async, p=TURN_SPEED_P, min_turn_angle=MIN_TURN_ANGLE, control_move_dir=True):
		global Af

		control_angle = offset_angle_to_control(a)
		STATES['turning'] = 'Turning to %1.2f'%control_angle
#		STATES['turning'] = 'Turning to %1.2f. Control angle: %1.2f'%(a, control_angle)

#		set_control_state()
		turn_angle = 0
		loggers.logDbg('Turning to %1.2f...'%control_angle)
		if control_move_dir and min_turn_angle<abs(control_angle):
			loggers.logDbg('before CAR_CONTROLLER.turn')
#			CAR_CONTROLLER.turn(control_angle, .7*pi, False)
			turn_speed = p*abs(control_angle)
			turn_angle = protocol.turn(control_angle, turn_speed, async)
#			time.sleep(1)
			loggers.logDbg('after CAR_CONTROLLER.turn')

#			while True:
#				turn_angle = CAR_CONTROLLER.turn(pi/8, ITER_TURN_SPEED)
#				time.sleep(0.1)

#			CAR_CONTROLLER.set_power_zerro()

#			Af += turn_angle

		return 

		state = 'turning'
		decl = 2*ANGLE_CONTROL_THRSH
		while decl > ANGLE_CONTROL_THRSH:
			if CONTROL_MOVE_DIR:
				CAR_CONTROLLER.turn(a)
#				time.sleep(0.5)
				if not EMULATE_MAV:
						master.recv_match(type='VFR_HUD', blocking=False)
						heading = master.messages['VFR_HUD'].heading
						decl = abs(heading*pi/180 - a)

			STATES[state] = "Turning to course %1.2f... course declination: %1.2f" % (a, decl)
			check_return_rc_control()

			if not EMULATE_MAV:
				yaw_pwm = proportional_control(heading*pi/180, a, Pyaw, STABLE_YAW)
				STATES['yaw'] = "Yaw: %d" % yaw_pwm
				if CONTROL_MOVE_DIR:
					control_copter(yaw=yaw_pwm)
				
		STATES[state] = 'Course angle %1.2f'%a
		control_copter(yaw=STABLE_YAW)


def plot_data(dir_dist, dir_ang, extra_sprites):
	if not VISUALIZE_LIDAR:
		return

	global lidar_data, lidar_points, lidar_cluster_list # _queuelidar_points

	primitives = [{"line": {'pos':(0,0), 'end': (dir_dist*cos(dir_ang), dir_dist*sin(dir_ang))}, "color":(0, 255, 0)}]
	if extra_sprites!=None:
		primitives.extend(extra_sprites)

	cl_max_cnt = len(lidar_cluster_list)/3*3

#	cl_by_color = cl_max_cnt/3
#	clr_block = 200/cl_by_color

#	print 'cl_max_cnt:', cl_max_cnt
#	print 'clr_block:', clr_block

	from PyQt4 import QtCore, QtGui # .Qt import GlobalColor
#	color_f = lambda ci, pos: 50+clr_block*(ci%(pos*cl_by_color/3))

#	loggers.logOutLen('lidar_cluster_list', lidar_cluster_list)

	for i, cl in enumerate(lidar_cluster_list):
#		ci =		
#		color = QtGui.QColor(ci%20)
		color = QtGui.QColor(QtCore.Qt.GlobalColor(3+i%19))
		rgb = color.getRgb()[:-1]
#		print 'color:', rgb
#		pdb.set_trace()

		assert cl!=None, 'Cluster must not be None!'
		primitives.append({"points": cl, "color": rgb, "size": 2})

#	pdb.set_trace()

#	assert lidar_points!=None, 'lidar_points must not be None!'
#	primitives.append({"points": lidar_points, "color": (250, 125, 125), "size": 2})

#	print "primitives: ", primitives
#	print "line count: ", len([p for p in primitives if "line" in p]), "!!!!!!!!!!"

#	sl = [p for p in primitives if "size" in p and not isinstance(p['size'], int)]
#	assert len(sl)==0, 'string size!!! %s'%sl
	
	lidar_data_queue.put({'primetives': primitives})
#	lidar_data_queue.put({'sector': lidar_data, 'primetives': primitives})


def set_direction_move(protocol, angle, async=True, motion_p=MOTION_SPEED_P, min_speed=MIN_SPEED, max_speed=MAX_SPEED, turn_p=TURN_SPEED_P,
		min_turn_angle=MIN_TURN_ANGLE, control_move_dir=True, stop_before_turn=STOP_BEFORE_TURN):
		global Af, lidar_points

#		yaw_pwm = proportional_control(Af, a, Pyaw, STABLE_YAW)
#				control_copter(yaw=(1+sign(Af-a)*Myaw)*STABLE_YAW)

#		if VISUALIZE_LIDAR:
#			b = a+pi/2
#			pnts = {"points": lidar_points, "color": (0, 255, 0), "size": 3}
#
#			dl = 400
#			direction = {"line": {'pos':(0,0), 'end':(dl*cos(b), dl*sin(b))}, "color":(255, 0, 0)}
#			lidar_data_queue.put([pnts, direction])

		speed = None
		if stop_before_turn:
			protocol.set_offset(0)

		turn_to(protocol, angle, async, turn_p, min_turn_angle, control_move_dir)
		if stop_before_turn:
			protocol.set_offset(max_speed)
#			time.sleep(.3)

		rwlm.output_states(STATES)
				
#		Af = a
		
		return move(protocol, angle, motion_p, min_speed, max_speed, min_turn_angle)

def check_return_rc_control():
	rwlm.output_states(STATES)
	if EMULATE_MAV:
		return False

	res = False
	master.recv_match(type='HEARTBEAT', blocking=False)
	hb = master.messages['HEARTBEAT']

	master.recv_match(type='SYS_STATUS', blocking=False)
#	sys = master.messages['SYS_STATUS']
#	STATES['sys'] = 'nav_mode: %s status: %s'%(sys.nav_mode, sys.status)

	mode = hb.custom_mode # System: %d hb.system_status, 
	STATES['custom_mode'] = 'Base mode: %s Custom mode: %s'%(hb.base_mode, mode)
	if mode != CONTROL_MODE:
			STATES[COPTER_CONTROL_STATE] = 'RC in control'
			mav.rc_channels_override_send(master.target_system, master.target_component, *([ 0 ]*8))
			res = True
			
	#STATES['hb'] = "HEARTBEAT: "+hb
	return res


def add_line(x, y, width, height, color='k'):
		ax.add_patch(Rectangle((x, y), width, height, color=color, fill=True))

if USE_MATPLOTLIB:
	fig = plt.figure(1,figsize=FIG_SIZE)#

#SELECTED_COLUMNS = [RES_COLUMN] # [name for name in SELECTED_NUM_COLUMNS if name!=x_col_name]
#COLORS = ('b', 'g', 'r', 'c', 'm', 'y', 'k', 'w')

	ax = fig.add_subplot(111, aspect='equal')
#ax.aspect=‘equal’
#		 logOutLen('Total group list', group_names)

	add_line(0, 0, BARRIER_THICK, BOX_HEIGHT)
	add_line(0, BOX_HEIGHT, BOX_WIDTH, BARRIER_THICK)
	add_line(BOX_WIDTH, 0, BARRIER_THICK, BOX_HEIGHT)
	add_line(0, 0, BOX_WIDTH, BARRIER_THICK)

#plt.show()

step = 0
default_step = .1
x_delta = default_step
y_delta = -default_step

Af = 0 # Угол движения (вперёд)
move_dir = Af
MARKER_CENTER = .5
INITIAL_POSITIONING = True

if USE_MATPLOTLIB:
	copter, arrow = get_copter(*COPTER_START_POS)
	for patch in (copter, arrow):
		ax.add_patch(patch)

	ax.set_title(u'Тест движения и поворотов')

	ax.autoscale_view(True)
	ax.plot()

s = None
CAR_CONTROLLER = Protocol()
CAR_CONTROLLER.set_pid_settings(0, 2, 0.2, 0.1)

def wait_heartbeat(m):
		'''wait for a heartbeat so we know the target system IDs'''
		print("Waiting for APM heartbeat")
		msg = m.recv_match(type='HEARTBEAT', blocking=True)
		print("Heartbeat from APM (system %u component %u)" % (m.target_system, m.target_component))
		return m.target_system, m.target_component
#		 return msg


@pu.functionThreader
#@pu.functionProcessWrapper
def lidar_data_visualize(queue):
		from lidar_frame.lidar_frame import main
		main(queue)

def set_car_motion_speed(protocol, angle, p=MOTION_SPEED_P, min_speed=MIN_SPEED, max_speed=MAX_SPEED, min_turn_angle=MIN_TURN_ANGLE):
	speed = min_speed+p/abs(angle) if min_turn_angle<abs(angle) else max_speed
	STATES['speed'] = 'Motion speed: %1.2f'%speed
	if CONTROL_MOVE_DIR: 
		protocol.set_offset(speed)

	return speed

lidar_data_queue = None
def control(rpi_host, iter_num=10000000, max_queue_size=None):
	global s, lidar_data, lidar_data_queue, lidar_queue
#	from Queue import Queue

	if CONTROL_MOVE_DIR and rpi_host:
		connect(rpi_host)

	if not EMULATE_SENSORS:
		if USE_LOCAL_LIDAR:
			from lidar.lidar import Lidar
			s = Lidar(pu.md.Queue(1))
			s.start()
		else:
			s = SensorsClient(rpi_host, 8080,  serialization="mesgpack")

	if VISUALIZE_LIDAR:
		lidar_data_queue = pu.md.Queue(max_queue_size)
#		print "lidar_data_queue: ", lidar_data_queue
		lidar_data_visualize(lidar_data_queue)

	loggers.logOut('Working...')
	if EMULATE_SENSORS:
		global stream
		import cPickle as pickle
		file_path = os.path.join(loggers.SCRIPT_FOLDER, 'data.dat')
		stream = pickle.Unpickler(open(file_path, "rb"))
		lines_before = None
	else:
		lidar_worker()
		
#	if not EMULATE_SENSORS:
#		print 'Data:', data
#		print 'Right wall distance: %1.2f'%get_average_sector(data, 90, 10)

	if not EMULATE_SENSORS:
		# Waiting for the first lidar data
		while lidar_data is None: pass

	loggers.logDbg('Setting offset')
	if USE_MATPLOTLIB:
		ani = animation.FuncAnimation(fig, process_graphics, frames=20, blit=True)
		plt.show()
	else:
		for i in xrange(iter_num):
			if EMULATE_SENSORS:
				process_lidar_data()

			if 0<MAIN_CYCLE_SLEEP:
				time.sleep(MAIN_CYCLE_SLEEP)
	
			decisions = None
			decisions = rwlm.move(lidar_data, lidar_cluster_list)
			rwlm.output_states(STATES)	
			if decisions is None:
				continue

			angle = decisions['turn_angle']
			STATES.update(decisions['states'])

#			print "line count: ", len([p for p in primitives if "line" in p]), "!!!!!!!!!!"
			
			speed = set_direction_move(CAR_CONTROLLER, angle, ASYNC_TURNS)
			plot_data(600*speed, angle+pi/2, decisions['primitives'])
			rwlm.output_states(STATES)	


def get_mavlink_modem_connection(dev_num):
	return mavutil.mavlink_connection('/dev/ttyUSB%d'%dev_num, baud=57600, source_system=253) #, dialect="ardupilotmega"

rnd.seed()
# create a mavlink serial instance
if not EMULATE_MAV:
	try:
		master = get_mavlink_modem_connection(0)
	except:
		master = get_mavlink_modem_connection(1)

	mav = master.mav
	print 'wait for the heartbeat msg'
	system, target_component = wait_heartbeat(master)

#	print 'Requesting ALL data streams...'
#	mav.request_data_stream_send(system, target_component, mavutil.mavlink.MAV_DATA_STREAM_ALL, 100, 1)

	print 'Requesting HUD data stream...'
	mav.request_data_stream_send(system, target_component, mavutil.mavlink.MAV_DATA_STREAM_EXTRA2, 10, 1)

	print 'Requesting data_stream MAV_DATA_STREAM_EXTRA1...'
	mav.request_data_stream_send(system, target_component, mavutil.mavlink.MAV_DATA_STREAM_EXTRA1, 10, 1)

	print 'Waiting for the first VFR_HUD message...'
	master.recv_match(type='VFR_HUD', blocking=True)

	print 'Waiting for the first ATTITUDE message...'
	master.recv_match(type='ATTITUDE', blocking=True)

	if ARM_MOTORS:
		master.arducopter_arm()
		print 'Waiting for motors to arm...'
		master.motors_armed_wait()
		print 'Motors armed'

def get_average_sector(data, angle_deg, sector_deg):
	values = data[0]['values']
	half_sect = sector_deg/2
	if angle_deg<half_sect:
		sector_values = values[angle_deg-half_sect:]
		sector_values.extend(values[0:angle_deg+half_sect])
	else:
		sector_values = values[angle_deg-half_sect:angle_deg+half_sect]

	sector_data = [l for l in sector_values if MIN_LIDAR_DISTANCE< l <MAX_LIDAR_DISTANCE]
	if len(sector_data)==0:
#			print 'Sector %d %d have no valid values!'%(angle_deg, sector_deg)
		return lidar_dist_to_metrics(MAX_LIDAR_DISTANCE)

#	print 'sector_data for', angle_deg, ':', sector_data
	return sum(l/100 for l in sector_data)/len(sector_data)

#LOCK = pu.threading.Lock()

lidar_data = None
lidar_points = None
lidar_lines = None
lidar_cluster_list = None
stream = None
def process_lidar_data():
	global s, lidar_data, lidar_data_queue, lidar_lines, lidar_cluster_list, lidar_points, stream

	data = None
	if not EMULATE_SENSORS:
		while data is None or len(data['values'])!=360:
			if USE_LOCAL_LIDAR:
				data = s.out_queue.get()
			else:
				data = s.ik_get_sector(1)[0]
	else:
		sensors = {}#{'ik_distance': measure_distance(x, y, -ORT), 'distance': measure_distance(x, y, 0), 'height': measure_distance(x, y, 0)}
#			data = {'values': [rnd.randrange(50, 550) for i in range(360)]}
		try:
			while data is None:
				data = stream.load()
		except EOFError:
			return

#	with LOCK:
	lidar_data = data
	lidar_cluster_list = rwlm.get_clusters(lidar_data)
#	loggers.logOutLen('lidar_cluster_list', lidar_cluster_list)


@pu.functionThreader
def lidar_worker():
	while True:
		process_lidar_data()


def get_nearest_line_dir(flt=lambda x: True):
	'Вернуть направление ближайшей линии'

	loggers.logOutLen('lidar_lines', lidar_lines, level=loggers.DEBUG)
	if len(lidar_lines)<1:
		return

#	set_control_state("")
	with LOCK:
		flt_lines = filter(flt, lidar_lines)

#	print 'flt_lines:', flt_lines
	distances = [(line_dict['distance'], line_dict['dir'], line_dict['normal']) for i, line_dict in enumerate(flt_lines)]

	distances.sort(key=lambda x: x[0])
#	print 'distances:', [d[0] for d in distances]
#	print 'Dangerous distances:', [(d[0], radians(d[2].get_angle())) for d in distances if d[0]<delta*100]

#	angles = [radians(d['normal'].get_angle()) for d in lidar_lines]
#	print 'angles:', angles
#	print 'filtered angles:', [radians(d['normal'].get_angle()) for d in flt_lines]

	if 0<len(distances):
		norm = distances[0][2]
#		norm_angle = radians(norm.get_angle())
#		anti_norm_angle = pi+norm_angle
		return distances[0][0], pi+radians(norm.get_angle())


Lf = 6
Lr = 6
Alt = 0
def right_wall_motion(x, y):
	time.sleep(MAIN_CYCLE_SLEEP)

	def initial_position():
		'Начальное позиционирование'

	if not EMULATE_MAV:
		master.recv_match(type='ATTITUDE', blocking=False)
		att = master.messages['ATTITUDE']
		STATES['pitchroll'] = 'Pitch: % .1f Roll: % .1f'%(att.pitch, att.roll)

	loggers.logDbg('before check_return_rc_control')
	check_return_rc_control()
	loggers.logDbg('after check_return_rc_control')

	global INITIAL_POSITIONING, WALL_ROUNDING_ANGLE, DEFAULT_WALL_ROUNDING_ANGLE_STEP, step, Af, lidar_lines, Lf, Lr, Alt
	step = default_step

	sensors = {}
	sensors['marker'] = None
	marker_state = sensors['marker'] if not EMULATE_SENSORS else None

#	loggers.logDbg('')
#	if not THREAD_LIDAR_PROCESSING:

#	STATES['s'] = 'sensors: %s'%sensors
#	print 'data:', data
#	print 'dist_4:', dist_4

	if not EMULATE_MAV:
		if abs(att.pitch) < MAX_SENSOR_PITCH:
			Lf = sensors['height']/100 # measure_distance(x, y, 0)

		if abs(att.pitch) < MAX_SENSOR_PITCH and abs(att.roll) < MAX_SENSOR_ROLL:
			Alt = sensors['distance']/100
	else:
#		Lf = sensors['height']/100
		Alt = 2 # sensors['distance']/100

	STATES['direct'] = 'Af: %1.2f'%Af
	STATES['us'] = 'Front: %1.2f'%Lf
	STATES['ir'] = 'Right: %1.2f'%Lr

#	print "marker_state:", marker_state
	STATES['marker'] = 'Marker: %s'%marker_state

	if marker_state!=None:
		mx, my = marker_state['center']
		if Dh < my:
			STATES[ALT_CONTROL] =  'Loosing marker. Lowering...'
			set_alt(x, y, Alt-da)
			return (x, y)

		dx = MARKER_CENTER-mx
		dx = dx if dx !=0 else 1
		marker_direct = int(dx/abs(dx))
		set_control_state("Marker detected! Moving towards it...")

		return set_direction_move(x, y, Af+DEFAULT_WALL_ROUNDING_ANGLE_STEP*marker_direct)
		
	Ar = Af-ORT # Угол движения вправо
	STATES['turning'] = ''

#	import pdb

	set_alt(x, y, Malt)
	if Lf < Df:
		set_control_state("Turning left. We are at the front wall")
		return set_direction_move(x, y, Af+ORT)
					
	if Dr < Lr:
		# Расстояние до правой стены больше порога

		#return initial_position()

		if WALL_ROUNDING_ANGLE == 0:
			if INITIAL_POSITIONING:
				INITIAL_POSITIONING = False
				return initial_position()
			else:
				if Dr+dr < Lr:
					WALL_ROUNDING_ANGLE = DEFAULT_WALL_ROUNDING_ANGLE_STEP
					set_control_state("Right barrier rounding...")
					return set_direction_move(x, y, Af-WALL_ROUNDING_ANGLE)
#	else:
#						 step = .1*default_step
		
#		set_control_state("Turning left") # WTF???
#		return set_direction_move(x, y, Ar-pi)

	WALL_ROUNDING_ANGLE = 0
	INITIAL_POSITIONING = False
	if Lr < Dr-dr:
		set_control_state("Moving from right wall. Too close")
		return set_direction_move(x, y, Af+DEFAULT_WALL_ROUNDING_ANGLE_STEP)
#		return move(x, y, Af+ORT)
	
	if Lf < Df and Dr-dr < Lr < Dr+dr:
		set_control_state("Turning Left. We are in the corner")
		return set_direction_move(x, y, Af+ORT)
					
	set_control_state("Moving forward")
#	pdb.set_trace()
	return #move(x, y, Af)


def set_control_state(state):
	STATES[CONTROL_STATE] = '%35s'%state


def profile():
	import cProfile, pstats

	profiling_stats = 'flight_control.stats'
	cProfile.run('control(10)', profiling_stats)
	stats = pstats.Stats(profiling_stats)
	stats.sort_stats('cumulative')
	print '\n'
	stats.print_stats(20)


#get_next_coords = perspective_motion # right_wall_motion

def connect(rpi_host, timout=2):
	loggers.logOut('Connecting to control service...')
	if USE_LOCAL_LIDAR:
		CAR_CONTROLLER.connect(0, {"port": "/dev/ttyUSB0", "baudrate":115200, "timeout":2, "writeTimeout":2})
	else:
		CAR_CONTROLLER.connect(1, {"host": rpi_host, "port": 1111})

	loggers.logOut('Raspberry connected. Waiting for initialization %d seconds...'%timout)
	time.sleep(timout)
			

def stop(rpi_host, connect_rpi=True):

		if connect_rpi:
			connect(rpi_host, 1)

		loggers.logOut('Stopping car')
		CAR_CONTROLLER.set_power_zerro()

		loggers.logOut('Closing car control Protocol instance')
		CAR_CONTROLLER.close()


def simulate(iter_num=10000):
	global EMULATE_SENSORS, CONTROL_MOVE_DIR
#	from Queue import Queue

	EMULATE_SENSORS = True
	CONTROL_MOVE_DIR = False
	return control(None, iter_num, max_queue_size=1)


def oscillation_test(rpi_host, a=pi/2, async=True):
#	from Queue import Queue
	sl_time = 1
	connect(rpi_host)

	CAR_CONTROLLER.set_offset(MOTION_SPEED)
	while True:
		turn_to(a, async)
		time.sleep(sl_time)
		turn_to(-a, async)
		time.sleep(sl_time)
		

if __name__ == "__main__":
#loggers.configureRotatingFileLogger(sys.argv[1])
	loggers.configureRotatingFileLogger(sys.argv[1], minLogLevel=loggers.INFO, fileLogLevel=loggers.DEBUG)
#loggers.configureRotatingFileLogger(sys.argv[1], minLogLevel=loggers.DEBUG, fileLogLevel=loggers.DEBUG)

#loggers.logging.getLogger("PyQt4").setLevel(logging.INFO)
	try:
		eval(getTxtArgsCmd())
		loggers.logOut('Task finished')
	except Exception as ex:
#	except TypeError:
		func = eval(sys.argv[1])
		loggers.logExc('Usage: %s'%func.__doc__)

		stop('', connect_rpi=False)
		while True and not EMULATE_MAV:
			'Returning mavlink control to RC'
			try:
				mav.rc_channels_override_send(master.target_system, master.target_component, *([ 0 ]*8))
				break
			except Exception as ex:
				print ex

		raise
