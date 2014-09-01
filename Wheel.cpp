#include "Wheel.h"
const int Wheel::Wheel::min_speed = 240;
const int Wheel::Wheel::max_speed = 10;

Wheel::Wheel(int __forward_pin, int __backward_pin):
    speed(min_speed),
    last_time(millis()),
    pid(&error, &pid_power, 2, 0, 0.35),
    speed_control(false),
    forward_pin(__forward_pin),
    backward_pin(__backward_pin),
    power(0.0),
    abs_speed(30),
    pid_power(0.0),
    error(0.0)
{
    pid.SetOutputLimits(0,1);
    pinMode(forward_pin, OUTPUT);
    pinMode(backward_pin, OUTPUT);
    digitalWrite(backward_pin, LOW);
    digitalWrite(forward_pin, LOW);
}

void Wheel::set_power(double value)
{
    if (value > 1. )
        value = 1.;
    else if (value < -1.0)
        value = -1.0;

    if (value != power )
    {
        power = value;

        if ( value > 0. )
        {
            analogWrite(forward_pin, int(value * 255));
            digitalWrite(backward_pin, LOW);
        }
        else if ( value < 0.f )
        {
            analogWrite(backward_pin, int(-(value * 255)));
            digitalWrite(forward_pin, LOW);
        }
        else
        {
            digitalWrite(backward_pin, LOW);
            digitalWrite(forward_pin, LOW);
        }
    }
}


void Wheel::update()
{
    update_speed_value();
    error = get_speed() - abs_speed;

    if ( speed_control )
    {  
        pid.Compute();
        //Serial.print(" error:");
        //Serial.print(error);
        //Serial.print(" power:");
        //Serial.print(pid_power);
        //Serial.print("\n");
        set_power(pid_power);
    }
}

void Wheel::update_speed_value()
{
    if (get_speed() < min_speed ){
        unsigned long cur_time = millis();

        if (cur_time - get_last_time() > min_speed){
            set_speed(min_speed);
        }
    }
}



