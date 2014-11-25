# -*- coding: utf-8 -*-
__author__ = 'AlexLexx'

import math
from Vec2d import Vec2d

class LineFeaturesMaker:
    '''Преобразует сектро точек после лидара в нобор линий'''
    def __init__(self):
        #список направлений.
        self.directions = [(Vec2d(1.0, 0.0), Vec2d(0.0, 1.0)),
                      (Vec2d(0.0, 1.0), Vec2d(-1.0, 0.0)),
                      (Vec2d(-1.0, 0.0), Vec2d(0.0, -1.0)),
                      (Vec2d(0.0, -1.0), Vec2d(1.0, 0.0))]

    def sector_to_points_clusters(self, data, start_angle=math.pi/2.0, max_len=1000):
        '''Преобразует данные сектора кластеры точек
           Возвращаеть лист листов Vec2d
        '''
        return [[k,] for k in self.make_clusters(self.sector_to_points(data, start_angle, max_len))]

    def sector_to_lines_clusters(self, data, start_angle=math.pi/2.0, max_len=1000):
        '''Преобразует данные сектора в кластеры линий
            Возвращаеть лист листов Vec2d
        '''
        res = []
        for cluster in self.make_clusters(self.sector_to_points(data, start_angle, max_len)):
            #отсекаем кластеры меньше 5 точек.
            if len(cluster) < 5:
                continue
            res.append(self.split_and_merge_cluster(cluster))
        return res

    def linearization_clusters_data(self, clusters_list):
        '''Преобразует данные кластеров точек в кластеры точек в которых точки в кластере выстроены вдоль направления кластера'''
        p_dist = 2.0
        
        for clusters in clusters_list:
            for i, cluster in enumerate(clusters):
                s_p = cluster[0]
                e_p = cluster[-1]
                direction = e_p - s_p
                l = direction.normalize_return_length()
                count = int(l / p_dist)
                
                #мало точек
                if count  < 2:
                    clusters[i] = [s_p, e_p]
                else:
                    clusters[i] = [s_p + direction * (p_dist * k) for k in range(count)]
                    clusters[i].append(e_p)
        return clusters_list

        
    def clusters_to_lines(self, clusters_list):
        '''Преобразует список кластеров в линии (start, stop, direction, normal)'''
        lines = []

        for clusters in clusters_list:
            for cluster in clusters:
                p1 = Vec2d(cluster[0])
                p2 = Vec2d(cluster[-1])
                d = (p2 - p1)
                l = d.normalize_return_length()
                n = d.perpendicular()
                center = p1 + d * l / 2.0
                distance = center.get_length()
                lines.append({"pos": p1,
                              "end": p2,
                              "dir": d,
                              "normal": n,
                              "length": l,
                              "center": center,
                              "distance": distance})
        return lines

    def search_similar(self, before_lines_frame, cur_lines_frame, max_angle=10., max_distance=10):
        '''Поиск похожих линий в кадрах'''
        similar_list = []

        for i, c_l in enumerate(cur_lines_frame):
            for j, b_l in enumerate(before_lines_frame):
                #сравним угол и расстояние
                angle = c_l["normal"].get_angle_between(b_l["normal"])
                if abs(angle) < max_angle:

                    #сравним расстояние.
                    dist = (c_l["distance"] - b_l["distance"])
                    if abs(dist) < max_distance:
                        similar_list.append((i,j, angle, dist))
                        break
        return similar_list

        #найдём ниболее верное угловое смещение.
        if len(similar_list):
            info = similar_list[0]
            max = cur_lines_frame[info[0]][4]
            angle = info[2]

            for info in similar_list[1:]:
                l = cur_lines_frame[info[0]][4]

                if l > max:
                    max = l
                    angle = info[2]

            return angle
        return 0

    def get_distances(self, lines):
        '''Найдём расстояние до передней, левой, задней, правой стенок.'''
        directions_res = [None, None, None, None]

        for i, d_desc in enumerate(self.directions):
            d_dir, d_norm = d_desc

            for l_desc in lines:
                #поиск проекций.
                l_p1 = l_desc["pos"]
                l_p2 = l_desc["end"]
                l_d = l_desc["dir"]
                l_n = l_desc["normal"]

                #проекция пересекает направление и нормали ок.
                if d_dir.dot(l_p1) >= 0.0 and d_dir.dot(l_p2) <= 0 and d_norm.dot(l_n) < 0.0:
                    k = self.line_intersection((l_p1, l_p2), (Vec2d(0,0), d_norm))

                    len = d_norm.dot(k)
                    directions_res[i] = len
                    break
        return directions_res

    def line_intersection(self, l1, l2):
        '''пересечение линий'''
        p1 = l1[0]
        p2 = l1[1]
        p3 = l2[0]
        p4 = l2[1]

        d = (p1.x - p2.x) * (p4.y - p3.y) - (p1.y - p2.y) * (p4.x - p3.x)
        da = (p1.x - p3.x) * (p4.y - p3.y) - (p1.y - p3.y) * (p4.x - p3.x)
        db = (p1.x - p2.x) * (p1.y - p3.y) - (p1.y - p2.y) * (p1.x - p3.x)

        if d  == 0:
            return None

        ta = da / float(d)
        tb = db / float(d)

        dx = p1.x + ta * (p2.x - p1.x)
        dy = p1.y + ta * (p2.y - p1.y)
        return Vec2d(dx, dy)


    def sector_to_points(self, data, start_angle=0, max_len=1000):
        '''Преобразует сектор в точки'''
        res = []
        da = data["angle"] / (len(data["values"]))
        data["values"].reverse()

        for i, value in enumerate(data["values"]):
            if max_len is not None and value > max_len:
                continue
            res.append(Vec2d(math.cos(start_angle + da * i) * value,
                              math.sin(start_angle + da * i) * value))
        return res

    def make_clusters(self, points):
        '''кластиризуем последовательности точек'''
        if len(points) == 0:
            return []

        s_pos = points[0]
        clasters = [[s_pos, ]]
        max_offset = 30

        def check(s_pos, c_pos):
            '''проверка группировки в кластер, по максимальному шагу'''
            l = (s_pos - c_pos).get_length()
            #найдём среднюю длинну
            return l < max_offset

        #создадим кластеры
        for c_pos in points[1:]:
            if check(s_pos, c_pos):
                clasters[-1].append(c_pos)
            else:
                clasters.append([c_pos,])
            s_pos = c_pos

        #обьединим перный и последний кластер
        if len(clasters) >= 2:
            if check(clasters[0][0], clasters[-1][-1]):
                clasters[-1].extend(clasters[0])
                clasters.pop(0)
        return clasters

    def split_and_merge_cluster(self, cluster):
        '''преобразуем кластер точек в набор прямых'''

        def split(cluster, res):
            '''Рекурсивное разделение кластера на маленькие линии'''
            threshold = 2

            #проверим максимальное отклонение от направления
            if len(cluster) > 2:
                #нормаль к прямой.
                s_pos = cluster[0]
                normal = (cluster[-1] - s_pos).perpendicular_normal()

                #поиск максимума
                max = 0
                max_i = 0

                for i, pos in enumerate(cluster[1:-1]):
                    p = abs(normal.dot(pos - s_pos))

                    if p > max:
                        max = p
                        max_i = i

                #делим кластер на два кластера
                if max > threshold:
                    split(cluster[:max_i + 2], res)
                    split(cluster[max_i + 1:], res)
                #не делим кластер
                else:
                    res.append(cluster)
            else:
                res.append(cluster)

        def merge(clusters):
            '''Обьединим соседние линии в одну если угол наклона не оч большой'''
            if len(clusters) > 1:
                threshold = 8

                first = clusters[0]
                i = 1
                no_merge = True

                while i < len(clusters):
                    cur = clusters[i]

                    v = (cur[-1] - first[0]).perpendicular_normal().dot(first[-1] - first[0])

                    #проверка обьединения.
                    if abs(v) < threshold:
                        first.extend(cur)
                        clusters.pop(i)
                        no_merge = False
                    else:
                        i +=1
                        first = cur

                #мёржим пока всё не склеиться
                if not no_merge:
                    merge(clusters)


        #разделим на отдельные прямые
        res = []
        split(cluster, res)
        merge(res)
        return res