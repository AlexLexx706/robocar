#include "car.h"
#include <Ultrasonic.h>
#include <Wire.h>
#include <I2Cdev.h>
#include <HMC5883L.h>
#include "vectoper.h"


#define SPEED 80
#define m1_f 3
#define m1_b 10

#define m2_f 6
#define m2_b 9

static int16_t mx, my, mz;
static HMC5883L mag;
static Ultrasonic ultrasonic(12, 13);


Car & Car::instance()
{
    static Car car;
    return car;
}

Car::Car():l_speed(0.f),r_speed(0.0),heading(0.0), start_time(millis()), dist_cm(0.f)
{
    direction[0] = 0.0;
    direction[1] = 0.0;
    
    pinMode(m1_f, OUTPUT);   // sets the pin as output
    pinMode(m1_b, OUTPUT);   // sets the pin as output
    pinMode(m2_f, OUTPUT);   // sets the pin as output
    pinMode(m2_b, OUTPUT);   // sets the pin as output

    digitalWrite(m1_f, LOW);
    digitalWrite(m1_b, LOW);

    digitalWrite(m2_f, LOW);
    digitalWrite(m2_b, LOW);


    Wire.begin();
    mag.initialize();

}

void Car::set_speed(Car::Wheel wheel, float value)
{
    if (value > 1.f )
        value = 1.f;
    else if (value < -1.0)
        value = -1.0;

    if ( wheel == RightWheel )
    {
        if (value != this->l_speed )
        {
            l_speed = value;

            if ( value > 0.f )
            {
                analogWrite(m1_f, int(value * 255));
                digitalWrite(m1_b, LOW);
            }
            else if ( value < 0.f )
            {
                analogWrite(m1_b, int(-(value * 255)));
                digitalWrite(m1_f, LOW);
            }
        }
    }
    else
    {
        if (value != r_speed )
        {
            r_speed = value;

            if ( value > 0.f )
            {
                analogWrite(m2_f, int(value * 255));
                digitalWrite(m2_b, LOW);
            }
            else if ( value < 0.f )
            {
                analogWrite(m2_b, int(-(value * 255)));
                digitalWrite(m2_f, LOW);
            }
        }
    }
}


void Car::update()
{
    //1. получаем направление.
    // To calculate heading in degrees. 0 degree indicates North
    mag.getHeading(&mx, &my, &mz);
    this->heading = atan2(my, mx);

    if( heading < 0 )
        heading += 2 * M_PI;
   
    //2. получим расстояние.
    if ( millis() > start_time + 100 )
    {       
        this->dist_cm = ultrasonic.Ranging(CM);
        start_time = millis();
    }
    
    //
    //Serial.println(this->heading);
} 
