#include "car.h"
#include <Ultrasonic.h>
#include <Wire.h>
#include <I2Cdev.h>
#include "vectoper.h"

Ultrasonic ultrasonic(D7, D8);


Car & Car::instance()
{
    static Car car;
    return car;
}

Car::Car():
    ud_start_time(millis()),
    distance_cm(0.f)
{
 
}

void Car::update()
{
    //1. получаем направление.
   
    //2. получим расстояние.
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
