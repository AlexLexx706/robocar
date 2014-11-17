# -*- coding: utf-8 -*-
import time

class PID:
    """ Simple PID control.

        This class implements a simplistic PID control algorithm. When first
        instantiated all the gain variables are set to zero, so calling
        the method GenOut will just return zero.
    """
    def __init__(self):
        # initialze gains
        self.Kp = 0
        self.Kd = 0
        self.Ki = 0

        self.Initialize()

    def SetKp(self, invar):
        """ Set proportional gain. """
        self.Kp = invar

    def SetKi(self, invar):
        """ Set integral gain. """
        self.Ki = invar

    def SetKd(self, invar):
        """ Set derivative gain. """
        self.Kd = invar

    def SetPrevErr(self, preverr):
        """ Set previous error value. """
        self.prev_err = preverr

    def Initialize(self):
        # initialize delta t variables
        self.currtm = time.time()
        self.prevtm = self.currtm

        self.prev_err = 0

        # term result variables
        self.Cp = 0
        self.Ci = 0
        self.Cd = 0


    def GenOut(self, error):
        """ Performs a PID computation and returns a control value based on
            the elapsed time (dt) and the error signal from a summing junction
            (the error parameter).
        """
        self.currtm = time.time()               # get t
        dt = self.currtm - self.prevtm          # get delta t
        de = error - self.prev_err              # get delta error

        self.Cp = self.Kp * error               # proportional term
        self.Ci += error * dt                   # integral term

        self.Cd = 0
        if dt > 0:                              # no div by zero
            self.Cd = de/dt                     # derivative term

        self.prevtm = self.currtm               # save t for next pass
        self.prev_err = error                   # save t-1 error

        # sum the terms and return the result
        return self.Cp + (self.Ki * self.Ci) + (self.Kd * self.Cd)


if __name__ == '__main__':
    import pygame
    from math import sin, cos
    from Vec2d import Vec2d

    pid = PID()
    Ku = 1
    pid.SetKp(10)
    pid.SetKi(0)
    pid.SetKd(1)
    
    WHITE = (255,255,255)
    GREEN = (0, 255, 0)
    RED = (255, 0, 0)
    BLUE = (0, 0, 255)

    pygame.init()
    screen = pygame.display.set_mode((320, 240))
    pygame.display.set_caption(u"dynamic_model")
    done = False
    clock = pygame.time.Clock()
    center = (screen.get_size()[0] / 2, screen.get_size()[1] / 2)
    distance_width = 5
    us_distance = 50
    
    line_len = 100
    angle = 0.5
    I = 10.0  #момент инерции 
    M = 0   #момент силы
    a = 0.0  #угловое ускорение
    w = 0.0   #угловая скорость
    mouse_pos = Vec2d(0,0)

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            if event.type == pygame.MOUSEMOTION:
                mouse_pos = Vec2d(event.pos)

        screen.fill(WHITE)
        pygame.draw.rect(screen, GREEN, (center[0] - distance_width, center[1] - us_distance, distance_width * 2, us_distance))
        
        v1 = Vec2d(cos(angle), sin(angle)) #направление узла
        v2 = (mouse_pos - center).normalized() #направление мышки
        diff_angle = v1.get_angle_between(v2)
        
        M = pid.GenOut(diff_angle)
        
        #if abs(M) > 100:
        #    M = 100 if  M > 0 else -100
        
        dt = clock.get_time() / 1000.
        if dt < 0.1:
            a = M / I
            w = w + a * dt
            angle = angle + w * dt
        
        

        pygame.draw.line(screen,
                        RED,
                        center,
                        (int(center[0] + cos(angle) * line_len), int(center[1] + sin(angle) * line_len)),
                        2)
        
        pygame.draw.circle(screen, BLUE, mouse_pos, 10)

        pygame.display.flip()
        clock.tick(60)
    pygame.quit()
