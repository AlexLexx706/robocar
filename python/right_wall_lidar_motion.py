# coding: utf-8

from math import sin, cos, pi, radians#, copysign

from lidar.LineFeaturesMaker import LineFeaturesMaker as LFM 

DELTA = 70 # Базовое безопасное расстояние до стен, в см
WALL_ANALYSIS_DX_GAP = 20 # коридор по ширине робота, в котором точки классифицируются как препятствия
WALL_ANALYSIS_ANGLE = 90 # углы анализа точек внутри коридора
MIN_LIDAR_DISTANCE = 20 # Минимальное измеримое лидаром расстояние, в см
MAX_LIDAR_DISTANCE = 600 # Максимальное измеримое лидаром расстояние, в см
TRUSTABLE_LIDAR_DISTANCE = 400 # Максимальное достоверное измеримое лидаром расстояние, в см

MIN_CLUSTER_LEN = 1

MIN_GAP_WIDTH = 50 # Минимальная ширина прохода в см

#Df = delta # Расстояние до передней стенки, в метрах
Dr = 30 # Расстояние до правой стенки, в см
#dr = 0.1 # Коридор расстояния до правой стенки (+/-), в метрах
Da = .1 # Снижение высоты при подлёте к маркеру, в метрах
Dh = .7 # Порог расстояния от центра маркера до нижней границы кадра (в долях 1)

lfm = LFM()

def normalize_angle(a):
	'Приводит угол в диапазон [-pi, pi]'
	return (pi+a)%(2*pi)-pi

def xy_angle_to_control(a):
	return normalize_angle(a-pi/2)

def lidar_dist_to_metrics(d):
	return d/100.

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
	
	states = {}
	states['turning'] = ''

	idx_range = (-WALL_ANALYSIS_ANGLE, WALL_ANALYSIS_ANGLE)
	motion_corridor = lambda a, d: (-WALL_ANALYSIS_DX_GAP< d*cos(radians(90+a-WALL_ANALYSIS_ANGLE)) <WALL_ANALYSIS_DX_GAP) #and d[0] in index_range
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
				x=WALL_ANALYSIS_DX_GAP*s
				return {"line": {'pos':(x, 0), 'end': (x, dc)}, "color":(255, 255, 0), "width": 4}

			primitives = [wlf(s) for s in (-1,1)]
			primitives.append({"line": wall, "color":(255, 0, 0), "width": 1})
#			print 'primitives', primitives
			return {'turn_angle': ctrl_angle, 'primitives': primitives, 'states': states}

#			return set_direction_move(x, y, (anti_norm_angle%pi)*2, False)

	res_angle = 2*pi
	max_dist = MIN_LIDAR_DISTANCE
		

	states['control'] = "Moving forward"
	if lidar_clusters==None:
		states['control'] = "lidar_clusters==None"
		lidar_clusters = get_clusters(lidar_data)

#	print 'lidar_clusters:', lidar_clusters
	lidar_clusters_len = len(lidar_clusters)
#	states['control'] = "lidar_clusters_len: %d"%lidar_clusters_len
	
	selected_gap = None
	selected_gap_vec = None
	selected_gap_start = None
	selected_gap_width = 0
	for i in range(-1, lidar_clusters_len-1):
		cluster1 = lidar_clusters[i]
		cluster2 = lidar_clusters[i+1]

		gap = (cluster1[-1], cluster2[0])
		start, stop = gap 
		angles_deg = (start.get_angle(), stop.get_angle()) # %360
		angles = map(radians, angles_deg)
		gate_dists = map(lambda x: x.get_length(), gap)
		valid_angles = [a for a in angles if 0<=a<=pi]
		if len(valid_angles)<1:
#			print "No valid angles:", angles
			continue

		gap_vec = stop-start
		gap_width = gap_vec.get_length()
		if gap_width<MIN_GAP_WIDTH:
#			print "Gap width %d not valid"%gap_width
#			states['control'] = "Gap (%d,%d) not valid"%(gap_width, angle)
			continue

		rad_norm_angles = [a%(2*pi) for a in angles]
		min_angle = min(rad_norm_angles)
		gate_dist = gate_dists[rad_norm_angles.index(min_angle)]

		angle = min_angle + Dr/gate_dist
#		angle = min_angle + copysign(Dr/gate_dist, pi/2-min_angle)

#		print "rad_norm_angles:", rad_norm_angles, 'gate_dist:', gate_dist, 'angle:', angle

		states['control'] = "Found valid gap"
		dist = MAX_LIDAR_DISTANCE # max((point.get_length() for point in gap))
		if max_dist<dist or (dist==max_dist and angle<res_angle):
			max_dist = dist
			res_angle = angle
			selected_gap_width = gap_width
			selected_gap = gap
			selected_gap_vec = gap_vec
			selected_gap_start = start

#			print "angles:", angles, "angle:", angle
#			print "valid angles:", valid_angles
	
#	states['control'] = "Checking res_angle"
	if res_angle!=None:
		states['control'] = "res_angle!=None"
		control_angle = xy_angle_to_control(res_angle)
		states['control'] = "Going to gap angle %1.2f. Gap width: %1.2f"%(control_angle, selected_gap_width/100)

#		pdb.set_trace()
		points = [{
						"points": selected_gap,
						"color": (255, 0, 255, 125),
						"size": 10
				},]
		if selected_gap_vec is None:
			return

		return {'turn_angle': control_angle, 'primitives': points, 'states': states}
