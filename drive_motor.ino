//#include "car.h"
#include <Ultrasonic.h>
#include <Wire.h>
#include <I2Cdev.h>
#include <HMC5883L.h>
#include "printf.h"
#include "Wheel.h"

Wheel wheel1(4, 3, 10);
Wheel wheel2(5, 6, 9);


void setup() 
{ 
    Serial.begin(115200);
}

void loop() 
{
    //Car::instance().update();
    wheel1.update();
    wheel2.update();
    float speed = ((cos(millis()/5000.) + 1.f)/2.f)*80.f;
    wheel1.set_abs_speed(speed);
    wheel2.set_abs_speed(speed);
//    Serial.print("abs_speed:  ");
//    Serial.print(wheel1.get_abs_speed());
//    Serial.print(" speed:  ");
//    Serial.print(wheel1.get_speed());
//    Serial.print(" power  ");
//    Serial.print(wheel1.get_power());
//    Serial.print("\r\n");
} 
