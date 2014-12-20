# coding: utf-8

import time, pdb
from math import sin, cos, pi, radians, copysign

from lidar.LineFeaturesMaker import LineFeaturesMaker as LFM 
import loggers

DELTA = 150 # Базовое безопасное расстояние до стен, в см
WALL_ANALYSIS_GAP = 15 # коридор по ширине робота, в котором точки классифицируются как препятствия
WALL_ANALYSIS_ANGLE = 90 # углы анализа точек внутри коридора
MIN_LIDAR_DISTANCE = 20 # Минимальное измеримое лидаром расстояние, в см
MAX_LIDAR_DISTANCE = 600 # Максимальное измеримое лидаром расстояние, в см
TRUSTABLE_LIDAR_DISTANCE = 400 # Максимальное достоверное измеримое лидаром расстояние, в см

MIN_CLUSTER_LEN = 1

MIN_GAP_WIDTH = 50 # Минимальная ширина прохода в см
MIN_RAD_GAP_WIDTH = 3 # Минимальная "радиальная" ширина прохода в см (по длине сектора)
MIN_GAP_ANGLE = .1 # Минимальная угловая ширина прохода в радианах

AVOID_WALLS = True
AVOID_WALLS = False

ABSOLUTE_WALL_AVOIDANCE = True
#ABSOLUTE_WALL_AVOIDANCE = False

#Df = delta # Расстояние до передней стенки, в метрах
Dr = 15 # Расстояние до правой стенки, в см
#dr = 0.1 # Коридор расстояния до правой стенки (+/-), в метрах
Da = .1 # Снижение высоты при подлёте к маркеру, в метрах
Dh = .7 # Порог расстояния от центра маркера до нижней границы кадра (в долях 1)

lfm = LFM()

def init():
	return
	loggers.configureDefaultLogger()

def normalize_angle(a):
	'Приводит угол в диапазон [-pi, pi]'
	return (pi+a)%(2*pi)-pi

def xy_angle_to_control(a):
	return normalize_angle(a-pi/2)

def lidar_dist_to_metrics(d):
	return d/100.

last_os_call = time.time()
def output_states(states):
	global last_os_call
	if time.time() - last_os_call < .05:
		return

#	print 'outputting states'

	loggers.logOut(' '.join(states.values()))
#	sys.stdout.write("\r%s %150s" % (time.strftime('%H:%M:%S'), ' '.join(STATES.values())))
	last_os_call = time.time()

def get_nearest_point_dir(flt, index_range, lidar_data):
	'Вернуть направление ближайшей точки'

#	loggers.logOutLen('lidar_lines', lidar_lines, level=loggers.DEBUG)
#	if len(lidar_lines)<1:
#		return

#	set_control_state("")
#	print 'lidar_data:', lidar_data['values']

	values = lidar_data['values']
	lidar_points = [values[i] for i in range(*index_range)] if index_range != None else list(values)

#	print 'lidar_points len:', len(lidar_points)
	flt_values = [d for a,d in enumerate(lidar_points) if flt(a,d)]
#	print 'flt point Xs:', [d*cos(radians(90+i+index_range[0])) for i, d in enumerate(lidar_points)]
#	print 'flt_values len:', len(flt_values)#, 'points:', lidar_points
	if len(flt_values)<1:
		return	

#	print 'flt_values:', flt_values
	min_dist = min(flt_values)
	
	angle = radians(lidar_points.index(min_dist)+index_range[0])+pi/2
#	pdb.set_trace()

#	print 'min_dist:', min_dist, 'angle:', angle
	return min_dist, angle

def get_clusters(lidar_data):
#	print 'lidar_data:', lidar_data
	lidar_points = lfm.sector_to_points(lidar_data, max_radius=TRUSTABLE_LIDAR_DISTANCE)

#	print 'lidar_points:', lidar_points
	spc = lfm.sector_to_points_clusters(lidar_points, min_cluster_len=MIN_CLUSTER_LEN)

	return spc

#	with LOCK:
#		lidar_clusters = []
#		for l in cluster_list:
#			lidar_clusters.extend(l)

#			STATES['lidar_clusters'] = 'lidar_clusters: %s'%lidar_clusters

#			lidar_lines = lfm.clusters_to_lines(cluster_list)
#			print 'lidar_lines: ', lidar_lines
#	if EMULATE_SENSORS:
#		time.sleep(.3)

def move(lidar_data, lidar_clusters=None):
	'''
	lidar_data - сырые данные с лидара
	lidar_clusters - отфильтрованный список кластеров
	'''
	
	result = None

	states = {}
	states['turning'] = ''

	if AVOID_WALLS:
		idx_range = (-WALL_ANALYSIS_ANGLE, WALL_ANALYSIS_ANGLE)
		motion_corridor = lambda a, d: (-WALL_ANALYSIS_GAP< d*cos(radians(90+a-WALL_ANALYSIS_ANGLE)) <WALL_ANALYSIS_GAP) #and d[0] in index_range
		mdd = get_nearest_point_dir(motion_corridor, idx_range, lidar_data)
		if mdd != None:
			dist, angle = mdd
			angle = normalize_angle(angle)
			if angle!=None and dist<DELTA:
				wall_ctrl_angle = xy_angle_to_control(angle)
				states['control'] = "Too close (%1.2f) to point @angle %1.2f. Moving away"%(lidar_dist_to_metrics(dist), wall_ctrl_angle)

				ctrl_angle = wall_ctrl_angle+pi/4
				da = pi/18
				wall = {'pos':(dist*cos(angle-da), dist*sin(angle-da)), 
								'end': (dist*cos(angle+da), dist*sin(angle+da))}

				def wlf(s): 
					dc = DELTA
					x=WALL_ANALYSIS_GAP*s
					return {"line": {'pos':(x, 0), 'end': (x, dc)}, "color":(255, 255, 0), "width": 4}

				primitives = [wlf(s) for s in (-1,1)]
				primitives.append({"line": wall, "color":(255, 0, 0), "width": 1})
#			print 'primitives', primitives
				result = {'turn_angle': ctrl_angle, 'primitives': primitives, 'states': states}

#			return set_direction_move(x, y, (anti_norm_angle%pi)*2, False)

	MAX_RES_ANGLE = 2*pi
	if result is None:
		res_angle = MAX_RES_ANGLE
		max_dist = MIN_LIDAR_DISTANCE
			

		states['control'] = "Moving forward"
		if lidar_clusters==None:
			states['control'] = "lidar_clusters==None. Calculating clusters..."
			lidar_clusters = get_clusters(lidar_data)

#	print 'lidar_clusters:', lidar_clusters
		lidar_clusters_len = len(lidar_clusters)
#	states['control'] = "lidar_clusters_len: %d"%lidar_clusters_len
		
		selected_gate = None
		selected_gate_vec = None
		selected_gate_start = None
		selected_gate_width = 0
		for i in range(-1, lidar_clusters_len-1):
			cluster1 = lidar_clusters[i]
			cluster2 = lidar_clusters[i+1]

			gate = (cluster1[-1], cluster2[0])
			start, stop = gate 
			angles_deg = (start.get_angle(), stop.get_angle()) # %360
			angles = map(lambda x: radians(x)%(2*pi), angles_deg)
			gate_dists = map(lambda x: x.get_length(), gate)

			valid_angles = filter(lambda a: 0<=a<=pi, angles) # 3*pi/2
			if len(valid_angles)<1:
				states['control'] = "No valid angles: %s"%angles
#			print "No valid angles:", angles
				continue

			gate_vec = stop-start
			gate_width = gate_vec.get_length()
			if gate_width<MIN_GAP_WIDTH:
#			print "Gate width %d not valid"%gate_width
#			states['control'] = "Gate (%d,%d) not valid"%(gate_width, angle)
				continue

			gate_sector = angles[0] - angles[1]

			gate_dist = min(gate_dists)
			min_dist_idx = gate_dists.index(gate_dist)
			min_dist_angle = angles[min_dist_idx]
			max_dist_angle = angles[1-min_dist_idx]
#		gate_dists[angles.index(min_dist_angle)]

			if abs(gate_sector)<MIN_GAP_ANGLE:
#		if gate_sector*gate_dist<MIN_RAD_GAP_WIDTH:
#			print "Gate sector %1.2f too narrow!"%gate_sector
#			states['control'] = "Gate (%d,%d) not valid"%(gate_width, angle)
				continue


			gap_dir = max_dist_angle - min_dist_angle
			angle = min_dist_angle + copysign(Dr/gate_dist, gap_dir)
#			angle = (max_dist_angle + min_dist_angle)/2

#		print "angles:", angles, 'gate_dist:', gate_dist, 'angle:', angle

			states['control'] = "Found valid gate"
			dist = MAX_LIDAR_DISTANCE # max((point.get_length() for point in gate))
			if max_dist<dist or (dist==max_dist and angle<res_angle):
#			print 'angles:', angles, 'min_dist_angle:', min_dist_angle
				max_dist = dist
				res_angle = angle
				angle_shift_sign = gap_dir
				selected_gate_dist = gate_dist
				selected_gate_width = gate_width
				selected_gate = gate
				selected_gate_vec = gate_vec
				selected_gate_start = start

#			print "angles:", angles, "angle:", angle
#			print "valid angles:", valid_angles
	
#	states['control'] = "Checking res_angle"
	if ABSOLUTE_WALL_AVOIDANCE:
		'Корректировка курса, если он пересекается с другими точками в заданном прямоугольнике'

		states['control'] = "res_angle!=None"
		corr_angle = res_angle if res_angle<2*pi else pi/2 # pi/2 - движение прямо, в случае если нет проходов
		intersect_points = []
		for cl in lidar_clusters:
			for point in cl:
				ca = radians(point.get_angle())%(2*pi)
				cl = point.get_length()
				if DELTA<cl or pi<ca:
					continue

				dc = cl*(corr_angle - ca)
				if abs(dc) < WALL_ANALYSIS_GAP:
					shift = copysign(WALL_ANALYSIS_GAP/cl, dc)
					intersect_points.append(point)

					print 'Shifting result angle %1.2f -> %1.2f ca: %1.2f dc: %1.2f cl: %1.2f'%(corr_angle, corr_angle+shift, ca, dc, cl)
#					if 1. < abs(shift):
#						pdb.set_trace()
					corr_angle += shift

		def wlf(s, a): 
			dc = DELTA
			dx=WALL_ANALYSIS_GAP*s
			ca = cos(a)
			sa = sin(a)
			b = pi/2-a
			sb = sin(b)
			return {"line": {'pos':(dx*sa, -sb), 'end': (dx+dc*ca, dc-sb)}, "color":(255, 255, 0), "width": 4}

		insct_points = { "points": intersect_points, "color": (255, 0, 0, 125), "size": 10 }

#		primitives = [wlf(s, corr_angle) for s in (-1,1)]
#		primitives.append(insct_points)
		primitives = [insct_points, ]

		control_angle = xy_angle_to_control(corr_angle)
		states['control'] = "Going to gate angle %1.2f. Gate width: %1.2f"%(control_angle, selected_gate_width/100)

#		pdb.set_trace()
		if selected_gate_vec != None:
			primitives.extend([{
							"points": selected_gate,
							"color": (255, 0, 255, 125),
							"size": 10
					},])

#		if selected_gate_vec != None:
		result = {'turn_angle': control_angle, 'primitives': primitives, 'states': states}
#	else:
#		states['control'] = "We are at the dead end. Going backwards"
#		result = {'turn_angle': pi, 'states': states}

	output_states(states)
	return result


if __name__ != '__main__':
	loggers.configureDefaultLogger()
