# -*- coding: utf-8 -*-
from Vec2d import Vec2d

class LineApproximation:
    def __init__(self, min_count, wnd):
        self.min_count = min_count
        self.wnd = wnd

    def approximate(self, points):
        count = self.min_count
        i = 0
        res = []

        while i + count < len(points):
            data = self.try_approximate(points[i: i + count])
            #обнаружена линия
            if data is not None:
                count = count + 1
                s_p = data[0]
                e_p = data[1]
            #продолжим апроксимацию
            else:
                #Сделали апроксимацию
                if count > self.min_count:
                    res.append( (1, (s_p, e_p)))
                    i = i + count
                #неудалось апроксимировать
                else:
                    res.append((0, points[i]))
                    i = i + 1
                count = self.min_count
        #Сделали апроксимацию
        if count > self.min_count:
            res.append((1, (s_p, e_p)))
        else:
            for p in points[i:]:
                res.append((0, p))
        return res

    def try_approximate(self, points):
        #1. рассчёт коэффициентов уравнения прямой. y = ax + b
        #                                           x = (y - b)/a
        sx = 0
        sxx = 0
        sy = 0
        sxy = 0

        for p in points:
            sx = sx + p[0]
            sy = sy + p[1]
            sxx = sxx + p[0] * p[0]
            sxy = sxy + p[0] * p[1]
        
        d = float(sx * sx - sxx * len(points))
       
        #вертикаль.
        if d == 0:
            return None
        #всё остальное.
        else:
            da = sy * sx - len(points) * sxy
            db = sx * sxy - sxx * sy
            a = da / d
            b = db / d

            #линия почти горизонтальная
            if abs(a) < 1.0:
                start_point = Vec2d(0.0, a * 0.0 + b)
                end_point = Vec2d(100.0, a * 100.0 + b)
            #линия почти вертикальная
            else:
                start_point = Vec2d((0.0 - b) / a, 0.0)
                end_point = Vec2d((100.0 - b) / a, 100.0)
            norm_dir = (end_point - start_point).normalized()
            perpendicular_norm = norm_dir.perpendicular()

            min = norm_dir.dot((Vec2d(points[0]) - start_point))
            s_value = min 
            max = min
            wnd_ok = True
            
            #найдём проверка условия апроксимации и поиск минимума и максимума
            for p in points[1:]:
                vector = p - start_point
                v = norm_dir.dot(vector)
                #print v
                h = abs(perpendicular_norm.dot(vector))

                #проверка условия апроксимации линией
                if h > self.wnd:
                    return None

                if v < min:
                    min = v
                elif v > max:
                    max = v
            
            #начало и конец
            if abs(s_value - min) < abs(s_value - max):
                sp = start_point + norm_dir * min
                ep = start_point + norm_dir * max
                return (sp, ep)
            else:
                sp = start_point + norm_dir * min
                ep = start_point + norm_dir * max
                return (ep, sp)
