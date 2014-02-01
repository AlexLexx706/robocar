#ifndef ALEX_CAR_H
#define ALEX_CAR_H
#include "Wheel.h"
#include "Ultrasonic.h"

class Car
{
public:
    Car();
    void update();
    Wheel wheel_left;
    Wheel wheel_right;

private:
    unsigned long ud_start_time;
    float distance_cm;
    Ultrasonic ultrasonic;
    
    void update_distance();
};

#endif
