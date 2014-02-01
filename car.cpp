#include "car.h"
#include <Wire.h>
#include <I2Cdev.h>
#include "Wheel.h"

Car::Car(): ud_start_time(millis()),distance_cm(0.f),wheel_left(4, 3, 10),wheel_right(5, 6, 9),ultrasonic(7, 8)
{ 
}

void Car::update()
{
    wheel_left.update();
    wheel_right.update();
    update_distance();
} 

void Car::update_distance()
{
    if ( millis() > ud_start_time + 100 )
    {       
        distance_cm = ultrasonic.Ranging(CM);
        ud_start_time = millis();
    }
}
