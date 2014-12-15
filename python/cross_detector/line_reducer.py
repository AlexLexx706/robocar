 # -*- coding: utf8 -*-
import math
from Vec2d import Vec2d
import logging

logger = logging.getLogger(__name__)


class LineReducer:
    def __init__(self):
        self.counter = 0
    
    def reduce(self, lines, max_angle=10, max_h=5, max_distance=5, short_lines=None):
        try:
            logger.debug("(lines:{}) ->".format(len(lines)))
            for l1 in lines:
                new_line = l1
                if new_line["valid"]:
                    for l2 in lines:
                        if l2["valid"] and new_line is not l2:
                            res_line = self.join_lines(new_line, l2, max_angle, max_h, max_distance)
                            if res_line is not None:
                                new_line["valid"] = False
                                l2["valid"] = False
                                new_line = res_line

                #замена элемента
                if id(l1) != id(new_line):
                    lines[lines.index(l1)] = new_line

            if short_lines is not None:
                res = [l for l in lines if l["valid"] and l["half_length"] * 2 >= short_lines]
            else:
                res = [i for i in lines if i["valid"]]
            return res
        finally:
            logger.debug("res:{}".format(len(res)))

    def reduse_by_intersection(self, lines, max_distance=None, angle_range=None):
        '''уберём не пересекающиеся линии'''
        if angle_range is None:
            for i, l1 in enumerate(lines):
                for j, l2 in enumerate(lines):
                    if l1 is not l2 and l1["valid"] and l2["valid"]:
                        if self.check_line_intersection(l1, l2, max_distance) is not None:
                            break
                else:
                    l1["valid"] = False
        else:
            for i, l1 in enumerate(lines):
                for j, l2 in enumerate(lines):
                    if l1 is not l2 and l1["valid"] and l2["valid"]:
                        if self.check_line_intersection(l1, l2, max_distance) is not None:
                            a = abs(l1["dir"].get_angle_between(l2["dir"]))
                            #проверка угла
                            if a >= angle_range[0] and a <= angle_range[1]:
                                break
                else:
                    l1["valid"] = False
        return [i for i in lines if i["valid"]]

    def reduse_by_intersection_pair(self, lines, max_distance, angle_range, true_cross_range=(0.3, 0.7)):
        '''уберём не пересекающиеся линии, сгрупперуем по парам '''
        result = []

        for i, l1 in enumerate(lines):
            l1["valid"] = False
            for j, l2 in enumerate(lines):
                if l2["valid"] and l1 is not l2:
                    for res in result:
                        if res[0] is l1 and res[1] is l2 or res[0] is l2 and res[1] is l1:
                            break
                    else:
                        pos = self.check_line_intersection(l1, l2, max_distance)
                        if pos is not None:
                            a = l1["dir"].dot(l2["dir"])

                            #проверка угла
                            if a >= angle_range[1] and a <= angle_range[0]:
                                #найдём направления относительно центра
                                #n1 = (l1["pos"] - pos[0]).normalized() if pos[1][0] > 0.5 else (l1["end"] - pos[0]).normalized()
                                #n2 = (l2["pos"] - pos[0]).normalized() if pos[1][1] > 0.5 else (l2["end"] - pos[0]).normalized()
                                n1 = l1["pos"] - pos[0] if pos[1][0] > 0.5 else l1["end"] - pos[0]
                                n2 = l2["pos"] - pos[0] if pos[1][1] > 0.5 else l2["end"] - pos[0]

                                true_cross = pos[1][0] >= true_cross_range[0] and pos[1][0] <= true_cross_range[1]\
                                             and pos[1][1] >= true_cross_range[0] and pos[1][1] <= true_cross_range[1]

                                result.append((l1, l2, true_cross, (pos[0], n1, n2)))
        return result

    def check_pair(self, p1, p2, min_proj=0.8, max_h=10):
        "определение смежных пар"
        if p1 is not p2:
            if p1[0] is p2[0] or p1[1] is p2[0] or p1[1] is p2[0] or p1[1] is p2[1]:
                return False
            #поиск параллельных пар
            res1 = self.check_parallel2(p1[0], p2[0])
            res2 = None

            if res1 is None:
                res1 = self.check_parallel2(p1[0], p2[1])

                if res1 is None:
                    return False

                res2 = self.check_parallel2(p1[1], p2[0])

                if res2 is None:
                    return False

                dir_1 = p1[3][1].dot(p2[3][2])
                dir_2 = p1[3][2].dot(p2[3][1])

                pos_1 = p1[3][1].dot(p2[3][0] - p1[3][0])
                pos_2 = p1[3][2].dot(p2[3][0] - p1[3][0])
            else:
                res2 = self.check_parallel2(p1[1], p2[1])

                if res2 is None:
                    return False

                dir_1 = p1[3][1].dot(p2[3][1])
                dir_2 = p1[3][2].dot(p2[3][2])

                pos_1 = p1[3][1].dot(p2[3][0] - p1[3][0])
                pos_2 = p1[3][2].dot(p2[3][0] - p1[3][0])

            #истинный крест
            if p1[2]:
                if res1[1] >= min_proj and res2[1] >= min_proj:
                    return True
            #истинный крест
            elif p2[2]:
                if res1[0] >= min_proj and res2[0] >= min_proj:
                    return True
            #проверка углов
            else:
                max_res1 = res1[0] if res1[0] > res1[1] else res1[1]
                max_res2 = res2[0] if res2[0] > res2[1] else res2[1]

                #1 не перекрывающиеся однонаправленные смотрят в разные стороны
                if res1[2] <= max_h and max_res1 < min_proj and dir_1 < 0.0 and pos_1 < 0.0 and max_res2 >= min_proj:
                    return True

                if res2[2] <= max_h and max_res2 < min_proj and dir_2 < 0.0 and pos_2 < 0.0 and max_res1 >= min_proj:
                    return True
            return False



    def draw_pair(self, p1, p2):
        import matplotlib.pyplot as plt
        p11 = p1
        p22 = p2

        data = p11[0]
        p1 = (int(data["pos"][0]), int(data["pos"][1]))
        p2 = (int(data["end"][0]), int(data["end"][1]))
        plt.plot((data["pos"][0], data["end"][0]), (data["pos"][1], data["end"][1]), color='k', linestyle='-', linewidth=1)
        plt.text(data["pos"][0], data["pos"][1], "0 0")

        data = p11[1]
        p1 = (int(data["pos"][0]), int(data["pos"][1]))
        p2 = (int(data["end"][0]), int(data["end"][1]))
        plt.plot((data["pos"][0], data["end"][0]), (data["pos"][1], data["end"][1]), color='k', linestyle='-', linewidth=1)
        plt.text(data["pos"][0], data["pos"][1], "0 1")


        data = p22[0]
        plt.plot((data["pos"][0], data["end"][0]), (data["pos"][1], data["end"][1]), color='k', linestyle='-', linewidth=1)
        plt.text(data["pos"][0], data["pos"][1], "1 0")

        data = p22[1]
        plt.plot((data["pos"][0], data["end"][0]), (data["pos"][1], data["end"][1]), color='k', linestyle='-', linewidth=1)
        plt.text(data["pos"][0], data["pos"][1], "1 1")


        plt.gca().invert_yaxis()
        plt.show()


    def grouping_crosses(self, cross_lines, min_proj=0.8):
        '''группируем пересекующиеся пары в группы'''
        groups = []
        crosses = []

        #1. группировка по парам
        for i, p1 in enumerate(cross_lines):
            gr = False
            for j, p2 in enumerate(cross_lines):
                for gr in groups:
                    if gr[0] is p1 and gr[1] is p2 or gr[0] is p2 and gr[1] is p1:
                        break
                else:
                    #logger.debug("check_pair i:{} j:{}".format(i, j))
                    if self.check_pair(p1, p2):
                        groups.append([p1, p2])
                        gr = True
                        #self.draw_pair(p1, p2)
                        #self.check_pair(p1, p2)

            #независимый крест
            if not gr and p1[2]:
                crosses.append([p1, ])

        #2. обьединения пар в большее
        for i, g1 in enumerate(groups):
            if g1 is None:
                continue

            for j, g2 in enumerate(groups):
                if g2 is None or g1 is g2:
                    continue

                #проверка общьности пар
                if g1[0] is g2[0]:
                    g1 = g1[-1:0:-1] + g2
                    groups[j] = None
                    groups[i] = g1

                    if g1[0] is g1[-1]:
                       del g1[-1]

                elif g1[0] is g2[-1]:
                    g1 = g2 + g1[1:]
                    groups[j] = None
                    groups[i] = g1

                    if g1[0] is g1[-1]:
                       del g1[-1]

                elif g1[-1] is g2[0]:
                    groups[j] = None
                    g1 = g1 + g2[1:]
                    groups[i] = g1
                    if g1[0] is g1[-1]:
                       del g1[-1]

                elif g1[-1] is g2[-1]:
                    groups[j] = None
                    g1 = g1 + g2[-2::-1]
                    groups[i] = g1

                    if g1[0] is g1[-1]:
                       del g1[-1]


        #3. проверка троек и истинных крестов
        for gr in groups:
            if gr is None:
                continue

            if len(gr) >= 3:
                crosses.append(gr)
            else:
                #проверка истинного креста
                for p in gr:
                    if p[2]:
                        crosses.append(gr)
                        break
        return crosses

    def reduce_groups(self, groups):
        #найдём из пар тройки и более
        pass

    def check_cross(self, lines, proj_max_angle=5, proj_offset_proc=0.5, dir_max_angle=5, dir_max_h=3):
        '''Определяем крест'''

        #1. найдём спроецированные пары
        pairs = self.create_projection_pairs(lines, max_angle=proj_max_angle, offset_proc=proj_offset_proc)

        #отбросим всё что меньше 4
        if len(pairs) < 4:
            return

        #2. найдём однонаправленные пары
        pairs = self.create_direction_pair(pairs, max_angle=dir_max_angle, max_h=dir_max_h)

        #return pairs

        cross_res = []
        used_pair = []
        #4. поиск точек пересечения пар.
        for p1 in pairs:
            for p2 in pairs:
                if p1 is not p2:
                    for pair in used_pair:
                        if pair[0] is p1 and pair[1] is p2 or pair[1] is p1 and pair[0] is p2:
                            break
                    else:
                        points = self.check_pair_intersection(p1, p2)
                        if points is not None:
                            used_pair.append((p1,p2))
                            cross_res.append(points)
        return cross_res

    def check_cross_2(self, lines, max_distance=10):
        '''Определяем крест'''

        #1. поиск угловых пар

        cross_groups = self.reduse_by_intersection_pair(lines,
                                                        max_distance=max_distance,
                                                        angle_range=(math.cos(30 / 180. * math.pi), math.cos(150 / 180. * math.pi)),
                                                        true_cross_range=(0.3, 0.7))
        #return [[gr,] for gr in cross_groups]
        return self.grouping_crosses(cross_groups, min_proj=0.8)



    def create_projection_pairs(self, lines, max_angle=10, offset_proc = 0.5):
        '''
        Создадим из линий пары линий: линии параллельны и проецируются друг на друга c с заданным перекрытием
        '''
        pairs = []
        min_dir_proj = math.cos(max_angle/180.0 * math.pi)

        #1. поиск пар
        for l1 in lines:
            for l2 in lines:
                if l1 is not l2:
                    for pair in pairs:
                        if pair[0] is l1 and pair[1] is l2 or pair[1] is l1 and pair[0] is l2:
                            break
                    else:
                        if self.check_parallel(l1, l2, min_dir_proj, offset_proc):
                            pairs.append((l1, l2))
        return pairs

    def create_direction_pair(self, pairs, max_angle=10, max_h=5):
        '''
        Создадим из двух пар линий общую, пары должны быть параллельны и расстояния между линиями минимальные
        '''
        #2. поиск однонаправленных пар
        result = []
        used_pairs = []

        for p1 in pairs:
            for p2 in pairs:
                if p1 is not p2:
                    for pair in used_pairs:
                        if pair[0] is p1 and pair[1] is p2 or pair[1] is p1 and pair[0] is p2:
                            break
                    else:
                        res = self.create_common_pair(p1, p2, max_angle, max_h)

                        if res is not None:
                            used_pairs.append(res[0])
                            result.append(res[1])
        return result

    def check_pair_intersection(self, pair_1, pair_2):
        '''
        Определение точек пересечения пар
        '''
        p1 = self.check_line_intersection(pair_1[0], pair_2[0])

        if p1 is None:
            return

        p2 = self.check_line_intersection(pair_1[0], pair_2[1])

        if p2 is None:
            return

        p3 = self.check_line_intersection(pair_1[1], pair_2[0])

        if p3 is None:
            return

        p4 = self.check_line_intersection(pair_1[1], pair_2[1])

        if p4 is None:
            return

        return (p1[0], p2[0], p3[0], p4[0])


    def check_line_intersection(self, l1, l2, max_distance = None):
        '''пересечение линий'''
        p1 = l1["pos"]
        p2 = l1["end"]
        p3 = l2["pos"]
        p4 = l2["end"]

        d = (p1.x - p2.x) * (p4.y - p3.y) - (p1.y - p2.y) * (p4.x - p3.x)
        da = (p1.x - p3.x) * (p4.y - p3.y) - (p1.y - p3.y) * (p4.x - p3.x)
        db = (p1.x - p2.x) * (p1.y - p3.y) - (p1.y - p2.y) * (p1.x - p3.x)

        if d  == 0:
            return

        ta = da / float(d)
        tb = db / float(d)

        if (ta >= 0 and ta < 1 and tb >= 0 and tb < 1):
            dx = p1.x + ta * (p2.x - p1.x)
            dy = p1.y + ta * (p2.y - p1.y)
            return (Vec2d(dx, dy), (ta, tb))

        if max_distance is None:
            return

        #используем отступ
        if ta < 0:
            if abs(ta * l1["length"]) > max_distance:
                return
        else:
            if ta * l1["length"] - l1["length"]  > max_distance:
                return

        if tb < 0:
            if abs(tb * l2["length"]) > max_distance:
                return
        else:
            if tb * l2["length"] - l2["length"]  > max_distance:
                return

        dx = p1.x + ta * (p2.x - p1.x)
        dy = p1.y + ta * (p2.y - p1.y)
        return (Vec2d(dx, dy), (ta, tb))

    def create_line_attributes(self, pos):

        if pos[0] <= pos[2]:
            s_pos = Vec2d(pos[0], pos[1])
            end = Vec2d(pos[2], pos[3])
            true_dir = Vec2d(pos[2] - pos[0], pos[3] - pos[1])
        else:
            s_pos = Vec2d(pos[2], pos[3])
            end = Vec2d(pos[0], pos[1])
            true_dir = Vec2d(pos[0] - pos[2], pos[1] - pos[3])

        dir = Vec2d(true_dir)
        length = dir.normalize_return_length()
        half_length = length / 2.
        normal = dir.perpendicular()
        self.counter += 1

        return {"pos": s_pos,
               "end": end,
               "true_dir": true_dir,
               "center": s_pos + dir * half_length,
               "half_length": half_length,
               "length": length,
               "dir": dir,
               "normal": normal,
               "valid": True}

    def check_parallel(self, l1, l2, min_dir_proj=0.9961946980917455, offset_proc=0.5):

        #1. сравниваем направления, различии не более 10 град
        if abs(l1["dir"].dot(l2["dir"])) < min_dir_proj:
            return False

        v_center = l2["center"] - l1["center"]

        #2. сравним перекрытие
        vv = abs(v_center.dot(l1["dir"]))
        l = (l1["half_length"] + l2["half_length"]) - vv

        #3.
        if l < 0:
            return False

        if l1["half_length"] < l2["half_length"]:
            if l / l1["length"] < offset_proc:
                return False
        else:
            if l / l2["length"] < offset_proc:
                return False
        return True

    def check_parallel2(self, l1, l2, min_dir_proj=0.9961946980917455):
        if l1 is l2:
            return (1.0, 1.0, 0.0)

        #1. сравниваем направления, различии не более 10 град
        dir = abs(l1["dir"].dot(l2["dir"]))

        if dir < min_dir_proj:
            return None

        v_center = l2["center"] - l1["center"]

        #2. сравним перекрытие
        vv = abs(v_center.dot(l1["dir"]))
        l = (l1["half_length"] + l2["half_length"]) - vv
        return (l / l1["length"], l / l2["length"], abs(l1["normal"].dot(v_center)))

    def create_common_pair(self, p1, p2, max_angle=10, max_h=5):
        #1. сравниваем направления, различии не более 10 град
        n_l1 = self.join_lines(p1[0], p2[0], max_angle=max_angle, max_h=max_h, max_distance=None)

        if n_l1 is None:
            n_l1 = self.join_lines(p1[0], p2[1], max_angle=max_angle, max_h=max_h, max_distance=None)

            if n_l1 is None:
                return
            n_l2 = self.join_lines(p1[1], p2[0], max_angle=max_angle, max_h=max_h, max_distance=None)
        else:
            n_l2 = self.join_lines(p1[1], p2[1], max_angle=max_angle, max_h=max_h, max_distance=None)

        if n_l2 is None:
            return
        return ((p1, p2), (n_l1, n_l2))

    def join_lines(self, l1, l2, max_angle=10, max_h=5, max_distance=5):
        max_angle = math.cos(max_angle / 180. * math.pi)

        # 1. сравниваем направления, различии не более 10 град
        if l1["dir"].dot(l2["dir"]) < max_angle:
            return

        v_center = l2["center"] - l1["center"]

        # 2. сравниваем близость по нормали не более 10 пикселов
        if abs(v_center.dot(l1["normal"])) > max_h:
            return
        
        # 3. сравниваем близость по направлению не более 10 пикселов
        if max_distance is not None:
            if abs(v_center.dot(l1["dir"])) > l1["half_length"] + l2["half_length"] + max_distance:
                return

        # 4. Создадим новое описание линии
        dir = (l1["true_dir"] + l2["true_dir"])
        dir.length = 1.0
        normal = dir.perpendicular()
        
        #1. определим границы линии по x
        v1 = (l2["pos"] - l1["pos"])
        v2 = (l2["end"] - l1["pos"])

        x1 = v1.dot(dir)
        x2 = v2.dot(dir)
        
        length = l1["length"]
        s_x = x1 if x1 < 0 else 0
        e_x = x2 if x2 > length else length
        length = e_x - s_x

        #2. определим смещение по нормали
        normal_offset = (normal.dot(l1["true_dir"]) + v1.dot(normal) + v2.dot(normal)) / 3.0

        pos = l1["pos"] + dir * s_x + normal * normal_offset
        end = pos + dir * length
        true_dir = end - pos
        self.counter += 1
        
        return {"pos": pos,
               "end": end,
               "true_dir": true_dir,
               "center": pos + true_dir / 2.0,
               "half_length": length / 2.0,
               "length": length,
               "dir": dir,
               "normal": normal,
               "valid": True}
   
    
if __name__ == "__main__":
    lr = LineReducer()
    [[8, Vec2d(7.17340734867, 216.122653978), Vec2d(57.3198265868, 145.225992297)], [10, Vec2d(43, 167), Vec2d(89, 102)]]    
    
    lines = [lr.create_line_attributes([7.17340734867, 216.122653978, 57.3198265868, 145.225992297]), lr.create_line_attributes([43, 167, 89, 102])]
    print lines
    print lr.reduce(lines)
    
