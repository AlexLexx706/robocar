# -*- coding: utf-8 -*-
import pygame
import json
import time
from LineApproximation import LineApproximation
import math

def make_window_function(N=40, a=2.0):
    import math
    res = []
    s = 0
    #строим граффик
    for i in range(N):
        n = -N / 2.0 + float(i)
        y = math.pow(math.e, (-1.0 / 2.0 * math.pow((a * n / (N / 2.0)), 2)))
        s = s + y
        res.append(y)
    return [i / s for i in res]


def draw_window_function(screen, color, center, width, height, data):
    for i, y in enumerate(data):
        y = int(center[1] - height * y)
        x = int(center[0] + width * ((i / float(len(data))) - 0.5) )
        pygame.draw.circle(screen, color, (x, y), 2)


def sector_to_data(data, center=(0, 0), window_fun=None, border=None, start_angle=0, angle_direction=True):
    #без оконной функции.
    if window_fun is None:
        res = []
    
        #start_angle = math.pi / 2.0 - data["angle"] / 2.0
        da = data["angle"] / (len(data["values"]))

        #if data["left"]:
        #    start_angle = start_angle + 0.13

        if angle_direction:
            for i, value in enumerate(data["values"]):
                ok = True
                if border is not None:
                    if value < border[0] or value > border[1]:
                        ok = False
                        continue

                x = int(center[0] + math.cos(start_angle + da * i) * value)
                y = int(center[1] - math.sin(start_angle + da * i) * value)
                res.append([x, y, ok])
        else:
            for i, value in enumerate(data["values"]):
                ok = True
                if border is not None:
                    if value < border[0] or value > border[1]:
                        ok = False
                        continue

                x = int(center[0] + math.cos(start_angle - da * i) * value)
                y = int(center[1] - math.sin(start_angle - da * i) * value)
                res.append([x, y, ok])        
        return res
    #Фильтруем оконной функцией.
    else:
        res = []
        da = data["angle"] / float(len(data["values"]))
        angle = da * (len(data["values"]) - len(window_fun))
        start_angle = math.pi / 2.0 - angle / 2.0
       
        if "left" in data and data["left"]:
            start_angle = start_angle + 0.13

        for i in range(0, len(data["values"]) - len(window_fun)):
            value = 0

            for j, d in enumerate(data["values"][i: i + len(window_fun)]):
                value = value + d * window_fun[j]
            
            ok = True
            if border is not None:
                if value < border[0] or value > border[1]:
                    ok = False
                    continue
                    
            x = int(center[0] + math.cos(start_angle + da * i) * value)
            y = int(center[1] - math.sin(start_angle + da * i) * value)
            res.append([x, y, ok])
        return res


def draw_sector(screen, color, data, center, window_fun=None, border=None, start_angle=0, angle_direction=True):
    pygame.draw.circle(screen, color, (int(center[0]), int(center[1])), 6)
    pygame.draw.line(screen, color, center, (center[0], 300), 2)
    #pygame.draw.lines(screen, color, False, sector_to_data(data, center, window_fun, max_radius), 3)
    s = None

    for p in sector_to_data(data, center, window_fun, border, start_angle, angle_direction):
        if s is not None:
            if p[2]:
                pygame.draw.line(screen, color, [s[0], s[1]], [p[0], p[1]], 2)
        s = p


def draw_sector_points(screen, color, data, center,  start_angle=0, angle_direction=True):
    pygame.draw.circle(screen, color, (int(center[0]), int(center[1])), 6)
    pygame.draw.line(screen, color, center, (center[0], 300), 2)
    
    for p in sector_to_data(data, center, start_angle=start_angle, angle_direction=angle_direction):
        pygame.draw.circle(screen, color, (int(p[0]), int(p[1])), 3)

def draw_greed(screen, color, center, width=50, height=50):
    x_offset = center[0] % width
    y_offset = center[1] % height

    if y_offset < 0:
        y_offset = height + y_offset
        
    if x_offset < 0:
        x_offset = width + x_offset

    size = screen.get_size()
    
    for i in range(int(size[0] / width)):
        x = x_offset + i * width
        pygame.draw.line(screen, color, [x, 0], [x, size[1]], 1)

    for i in range(int(size[1] / height)):
        y = y_offset + i * height
        pygame.draw.line(screen, color, [0, y], [size[0], y], 1)
        

def draw_approx(screen, color, approx_data):
    for d in approx_data:
        if d[0] == 0:
            pygame.draw.circle(screen, color, (int(d[1][0]), int(d[1][1])), 2)
        else:
            pygame.draw.line(screen, color, d[1][0], d[1][1], 2)

if __name__ == '__main__':
    # Initialize the game engine
    WHITE = [255, 255, 255]
    GREEN = [0, 255, 0]
    BLUE = [0, 0, 255]
    RED = [255, 0, 0]
    size = (600, 600)

    pygame.init()
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption(u"Test")
    done = False
    clock = pygame.time.Clock()
     
    st = time.time()
    data_index = 200
    true_data = json.loads(open("26_Apr_2014__00_27_54.json", "rb").read())
    center = [size[0] / 2, size[1] * 0.7]
    font = pygame.font.Font(None, 36)
    text = font.render("{0}".format(data_index), 1, (10, 10, 10))
    textpos = text.get_rect()
    
    approx = LineApproximation(20, 15)
    wnd = make_window_function(N=10)

    while not done:
     
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
        screen.fill(WHITE)
        screen.blit(text, textpos)
        #draw_window_function(screen, RED, center, 100, 600, make_window_function())

        if (time.time() - st) > 0.3:
            data_index = data_index + 1
            data_index = data_index % len(true_data)
            st = time.time()
            text = font.render("{0}".format(data_index), 1, (10, 10, 10))
            textpos = text.get_rect()
        
        draw_sector(screen, GREEN, true_data[data_index], center, wnd, 300)
        #offset_center = [center[0], center[1] + 10]
        #draw_sector(screen, RED, true_data[data_index], offset_center)
        #draw_approx(screen, BLUE, approx.approximate(sector_to_data(true_data[data_index], center, wnd)))

        pygame.display.flip()
        clock.tick(60)
    pygame.quit()