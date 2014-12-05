#!/usr/bin/python
# coding: utf-8

# Система управления
import sys, time, collections as coll, pdb

from math import sin, cos, pi, sqrt, radians
import random as rnd
#import numpy as np

from tcp_rpc.client import Client as SensorsClient
from lidar.LineFeaturesMaker import LineFeaturesMaker as LFM 
from car_controll.protocol import Protocol

import loggers
import procUtils as pu
from launcher import getTxtArgsCmd

PROFILE = False
#PROFILE = True

EMULATE_SENSORS = True
EMULATE_SENSORS = False

CONTROL_MOVE_DIR = True
#CONTROL_MOVE_DIR = False

MOTION_DEBUG = True

VISUALIZE_LIDAR = True
#VISUALIZE_LIDAR = False

EMULATE_MAV = True
#EMULATE_MAV = False

ARM_MOTORS = False

THREAD_LIDAR_PROCESSING = False
THREAD_LIDAR_PROCESSING = True

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
MOTION_SPEED = .5
ITER_TURN_SPEED = .5*pi
MIN_TURN_ANGLE = pi/36
WALL_ROUNDING_ANGLE = 0
MAIN_CYCLE_SLEEP = .3 # .5
WALL_ANALYSIS_ANGLE = 40
WALL_ANALYSIS_DX_GAP = 15
#WALL_ROUNDING_ANGLE = DEFAULT_WALL_ROUNDING_ANGLE_STEP

ASYNC_TURNS = False
#ASYNC_TURNS = True 

delta = .5 # Базовое безопасное расстояние до стен
Df = delta # Расстояние до передней стенки
Dr = Df # Расстояние до правой стенки
dr = 0.1 # Коридор расстояния до правой стенки (+/-)
Dh = .7 # Порог расстояния от центра маркера до нижней границы кадра (в долях 1)
da = .1 # Снижение высоты при подлёте к маркеру, в метрах

MIN_GAP_WIDTH = 100 # Минимальная ширина прохода в см

MIN_LIDAR_DISTANCE = 20 # Минимальное измеримое лидаром расстояние, в см
MAX_LIDAR_DISTANCE = 600 # Максимальное измеримое лидаром расстояние, в см

CONTROL_STATE = 'control'

lfm = LFM()
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

def lidar_dist_to_metrics(d):
	return d/100.

def xy_angle_to_control(a):
	return normalize_angle(a-pi/2)

def normalize_angle(a):
	'Приводит угол в диапазон [-pi, pi]'
	return (pi+a)%(2*pi)-pi

def offset_angle_to_control(a):
	return normalize_angle(a-Af)

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

def move(x, y, a):
		if not CONTROL_MOVE_DIR:
			return

		return

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


def turn_to(a, async):
		global Af

		control_angle = offset_angle_to_control(a)
		STATES['turning'] = 'Turning to %1.2f'%control_angle
#		STATES['turning'] = 'Turning to %1.2f. Control angle: %1.2f'%(a, control_angle)

#		set_control_state()
		turn_angle = 0
		loggers.logDbg('Turning to %1.2f...'%control_angle)
		if CONTROL_MOVE_DIR and MIN_TURN_ANGLE<abs(control_angle):
			loggers.logDbg('before CAR_CONTROLLER.turn')
#			CAR_CONTROLLER.turn(control_angle, .7*pi, False)
			turn_angle = CAR_CONTROLLER.turn(control_angle, ITER_TURN_SPEED, async)
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


def plot_data(dir_dist, dir_ang, *extra_sprites):
	if not VISUALIZE_LIDAR:
		return

#	global lidar_data_queuelidar_points

	pnts = {"points": lidar_points, "color": (0, 255, 0), "size": 3}

	direction = {"line": {'pos':(0,0), 'end': (dir_dist*cos(dir_ang), dir_dist*sin(dir_ang))}, "color":(0, 255, 0)}
	primitives = [pnts, direction]
	if extra_sprites!=None:
		primitives.extend(extra_sprites)

#	print primitives
#	pdb.set_trace()
	lidar_data_queue.put(primitives)


sign = lambda a: 1.*a/abs(a) if a !=0 else 1
def set_direction_move(x, y, a, async=True):
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

		if MOTION_DEBUG:
			time.sleep(.01)
			CAR_CONTROLLER.set_offset(0)
			time.sleep(.01)

		turn_to(a, async)
		if MOTION_DEBUG:
			time.sleep(.01)
			CAR_CONTROLLER.set_offset(MOTION_SPEED)
			time.sleep(.2)

		output_states()
				
#		Af = a
		return move(x, y, 0)

last_os_call = time.time()
def output_states():
	global last_os_call
	if time.time() - last_os_call < .05:
		return

#	print 'outputting states'

	loggers.logOut(' '.join(STATES.values()))
#	sys.stdout.write("\r%s %150s" % (time.strftime('%H:%M:%S'), ' '.join(STATES.values())))
	last_os_call = time.time()

def check_return_rc_control():
	output_states()
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
		from LidarFrame import main
		main(queue)

lidar_data_queue = None
def control(rpi_host, iter_num=10000000, max_queue_size=None):
	global s, lidar_data, lidar_data_queue
#	from Queue import Queue

	if CONTROL_MOVE_DIR:
		connect(rpi_host)

	if not EMULATE_SENSORS:
		s = SensorsClient(rpi_host, 8080)

	if VISUALIZE_LIDAR:
		lidar_data_queue = pu.md.Queue(max_queue_size)
		print "lidar_data_queue: ", lidar_data_queue
		lidar_data_visualize(lidar_data_queue)

	loggers.logOut('Working...')
	lidar_worker()
	if THREAD_LIDAR_PROCESSING and not EMULATE_SENSORS:
		pass
#		pu.startThread(lidar_worker)
	else:
		lidar_worker()

#	if not EMULATE_SENSORS:
#		print 'Data:', data
#		print 'Right wall distance: %1.2f'%get_average_sector(data, 90, 10)

	# Waiting for the first lidar data
	while lidar_data is None: pass

	loggers.logDbg('Setting offset')
	if 0<MOTION_SPEED:
		CAR_CONTROLLER.set_offset(MOTION_SPEED)

	if USE_MATPLOTLIB:
		ani = animation.FuncAnimation(fig, process_graphics, frames=20, blit=True)
		plt.show()
	else:
		for i in xrange(iter_num):
			get_next_coords(0,0)
			output_states()	


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

LOCK = pu.threading.Lock()

lidar_data = None
lidar_points = None
lidar_lines = None
lidar_cluster_list = None


@pu.functionThreader
def lidar_worker():
	global Lf, Lr, s, lidar_data, lidar_data_queue, lidar_lines, lidar_cluster_list, lidar_points

	if EMULATE_SENSORS:
		import cPickle as pickle
		stream = pickle.Unpickler(open(loggers.SCRIPT_FOLDER+'/data.dat', "rb"))
		lines_before = None
		

	while True:
		data = None
		if not EMULATE_SENSORS:
			while data is None or len(data[0]['values'])!=360:
				data = s.ik_get_sector(1)
		else:
			sensors = {}#{'ik_distance': measure_distance(x, y, -ORT), 'distance': measure_distance(x, y, 0), 'height': measure_distance(x, y, 0)}
#			data = [{'values': [rnd.randrange(50, 550) for i in range(360)]}]
			try:
				time.sleep(.3)
				data = [stream.load()]
			except EOFError:
				return

		with LOCK:
			lidar_data = data[0]

#		STATES['max_dist'] = 'lidar points max: %d'%max((p.get_length() for p in points))
		with LOCK:
			lidar_points = lfm.sector_to_points(lidar_data)
			cluster_list = [lfm.split_and_merge_cluster(cl) for l in lfm.sector_to_points_clusters(lidar_points) for cl in l]
#			cluster_list = [lfm.split_and_merge_cluster(cl) for l in lfm.sector_to_points_clusters(lidar_points) for cl in l if 5<=len(cl)]
			lidar_cluster_list = []
			for l in cluster_list:
				for cl in l:
					lidar_cluster_list.extend(lfm.split_and_merge_cluster(cl))

#			STATES['lidar_clusters'] = 'lidar_cluster_list: %s'%lidar_cluster_list

#			lidar_lines = lfm.clusters_to_lines(cluster_list)
#			print 'lidar_lines: ', lidar_lines

#	Lf = get_average_sector(data, 0, 20) # measure_distance(x, y, 0)
#	Lr = get_average_sector(data, 90, 10) # measure_distance(x, y, -ORT)*

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


def get_nearest_point_dir(flt=lambda x: True, index_range=None):
	'Вернуть направление ближайшей точки'

#	loggers.logOutLen('lidar_lines', lidar_lines, level=loggers.DEBUG)
#	if len(lidar_lines)<1:
#		return

#	set_control_state("")
#	print 'lidar_data:', lidar_data

	with LOCK:
#		values = list(lidar_data['values'])
		flt_values = filter(flt, enumerate(lidar_data['values']))

#	lidar_points = [flt_values[i] for i in range(*index_range)] if index_range!=None else flt_values

#	print 'lidar_points len:', len(lidar_points)#, 'points:', lidar_points

	if len(flt_values)<1:
		return	

	min_dist = min(flt_values)
	
	angle = radians(flt_points.index(min_dist)+index_range[0])+pi/2
#	pdb.set_trace()

#	print 'min_dist:', min_dist, 'angle:', angle
	return min_dist, angle


Lf = 6
Lr = 6
Alt = 0
def right_wall_motion(x, y):
	time.sleep(MAIN_CYCLE_SLEEP)

	def initial_position():
		'Начальное позиционирование'

		loggers.logOutLen('lidar_lines', lidar_lines, level=loggers.DEBUG)
		if 0<len(lidar_lines):
			set_control_state("Initial positioning")
			dist, direction, anti_norm_angle = get_minimal_distance_dir()
			INITIAL_POSITIONING = False
#				return set_direction_move(x, y, pi/18)
			if anti_norm_angle!=None and delta<dist:
				return set_direction_move(x, y, xy_angle_to_control(anti_norm_angle)) # get first distances item's normal

		return
#		return move(x, y, Ar)

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


def perspective_motion(x, y):
#	CAR_CONTROLLER.set_offset(MOTION_SPEED)
	if 0<MAIN_CYCLE_SLEEP:
		time.sleep(MAIN_CYCLE_SLEEP)
	
	STATES['turning'] = ''

	def line_angle_filter(x):
		xna = radians(x['normal'].get_angle())
		return -pi< xna <0

	def point_angle_filter(x):
		xa = radians(x.get_angle())
		return 0< xa <pi

#	mdd = get_nearest_line_dir(line_angle_filter)
	index_range = (-WALL_ANALYSIS_ANGLE, WALL_ANALYSIS_ANGLE)
	motion_corridor = lambda d: (-WALL_ANALYSIS_DX_GAP< d[1]*cos(radians(d[0])) <WALL_ANALYSIS_DX_GAP) and d[0] in index_range
	mdd = get_nearest_point_dir(motion_corridor)
	if mdd != None:
		dist, angle = mdd
		angle = normalize_angle(angle)
		metric_dist = lidar_dist_to_metrics(dist)
		if angle!=None and metric_dist<delta:
			wall_ctrl_angle = xy_angle_to_control(angle)
			set_control_state("Too close (%1.2f) to point @angle %1.2f. Moving away"%(metric_dist, wall_ctrl_angle))

			ctrl_angle = wall_ctrl_angle+pi/4
			da = pi/36
			wall = {'pos':(dist*cos(angle-da), dist*sin(angle-da)), 
							'end': (dist*cos(angle+da), dist*sin(angle+da))}

			plot_data(dist, ctrl_angle+pi/2, {"line": wall, "color":(255, 0, 0), "width": 3})
			return set_direction_move(x, y, ctrl_angle, ASYNC_TURNS)

#			return set_direction_move(x, y, (anti_norm_angle%pi)*2, False)

	res_angle = None
	max_dist = MIN_LIDAR_DISTANCE
		
	global lidar_cluster_list
	with LOCK:
		local_clusters = list(lidar_cluster_list)

	set_control_state("Moving forward")
	if local_clusters==None:
		set_control_state("local_clusters==None")
		return

#	print 'lidar_cluster_list:', local_clusters
	local_clusters_len = len(local_clusters)
#	set_control_state("local_clusters_len: %d"%local_clusters_len)
	
	selected_gap = None
	selected_gap_vec = None
	selected_gap_start = None
	selected_gap_width = 0
	max_gap_width = 0
	min_angle = pi
	for i in range(-1, local_clusters_len-1):
		cluster1 = local_clusters[i]
		cluster2 = local_clusters[i+1]
#		if len(cluster)<2:
#			set_control_state("Cluster list length < 2")
#			continue

		gap = (cluster1[-1], cluster2[0])
		start, stop = gap 
#		angle = radians(stop.get_angle_between(start)-start.get_angle())
		angles_deg = (start.get_angle(), stop.get_angle())
		angles = map(radians, angles_deg)
		valid_angles = [angle for angle in angles if 0<=angle<=pi]
		if len(valid_angles)<1:
#			print "No valid angles:", angles
			continue

		angle = sum(valid_angles)/len(valid_angles)
		gap_vec = stop-start
		gap_width = gap_vec.get_length()
		if max_gap_width<gap_width:
			max_gap_width = gap_width
#			STATES['max_gap_width'] = "Max gap width %1.1f at angle %1.1f"%(lidar_dist_to_metrics(gap_width), angle)
#			res_angle = angle

#		continue

		if gap_width<MIN_GAP_WIDTH:
#			print "Gap width %d not valid"%gap_width
#			set_control_state("Gap (%d,%d) not valid"%(gap_width, angle))
			continue

		set_control_state("Found valid gap")
		dist = MAX_LIDAR_DISTANCE # max((point.get_length() for point in gap))
		if max_dist<dist or (dist==max_dist and angle<res_angle):
			max_dist = dist
			res_angle = angle
			selected_gap_width = gap_width
			selected_gap = gap
			selected_gap_vec = gap_vec
			selected_gap_start = start

	
#	set_control_state("Checking res_angle")
	if res_angle!=None:
		set_control_state("res_angle!=None")
		control_angle = xy_angle_to_control(res_angle)
		set_control_state("Going to gap angle %1.2f. Gap width: %1.2f"%(control_angle, selected_gap_width/100))

#		pdb.set_trace()
#Отображает точки, в формате:
		points = {
            "points": selected_gap,
            "color": (0,0,255),
            "size": 10
        }
		plot_data((selected_gap_start+selected_gap_vec/2).get_length(), res_angle, points)

		return set_direction_move(x, y, control_angle, ASYNC_TURNS)
	
#	return move(x, y, Af)


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


get_next_coords = perspective_motion # right_wall_motion

#loggers.configureRotatingFileLogger(sys.argv[1])
loggers.configureRotatingFileLogger(sys.argv[1], minLogLevel=loggers.INFO, fileLogLevel=loggers.DEBUG)
#loggers.configureRotatingFileLogger(sys.argv[1], minLogLevel=loggers.DEBUG, fileLogLevel=loggers.DEBUG)

#loggers.logging.getLogger("PyQt4").setLevel(logging.INFO)

def connect(rpi_host, timout=2):
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
	global s, lidar_data, lidar_data_queue, EMULATE_SENSORS, CONTROL_MOVE_DIR
#	from Queue import Queue

	EMULATE_SENSORS = True
	CONTROL_MOVE_DIR = False
	return control('', iter_num, max_queue_size=1)


if __name__ == "__main__":
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
