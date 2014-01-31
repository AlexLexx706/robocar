//#include "car.h"
#include <Ultrasonic.h>
#include <Wire.h>
#include <I2Cdev.h>
#include <HMC5883L.h>
#include "printf.h"
#include "Wheel.h"

Wheel wheel1(4, 3, 10);


void setup() 
{ 
    Serial.begin(115200);
    //printf_begin();
    //Car::instance();
}

void loop() 
{
    //Car::instance().update();
    wheel1.update();
    float speed = cos(millis()/5000.);
    wheel1.set_power(speed);
    //wheel1.set_power(0.4);
    //Car::instance().set_speed(Car::LeftWheel, speed);
    //Car::instance().set_speed(Car::RightWheel, speed);
    Serial.print("abs_speed:  ");
    Serial.print(wheel1.get_abs_speed());
    Serial.print(" speed:  ");
    Serial.print(wheel1.get_speed());
    Serial.print(" power  ");
    Serial.print(wheel1.get_power());
    Serial.print("\r\n");
} 
