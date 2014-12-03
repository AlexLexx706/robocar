#include "Wheel.h"

#define MAX_COUNT 1500

Wheel::Wheel(int _pwm_pin, int _direction_pin):
    speed(0),
    pid(&error, &pid_power, 0.0001, 0, 0.00001),
    speed_control(false),
    pwm_pin(_pwm_pin),
    direction_pin(_direction_pin),
    power(0.0),
    abs_speed(30),
    pid_power(0.0),
    error(0.0),
    info_period(1000000),
    count(0),
    sign(1)
{
    pid.SetOutputLimits(-1,1);
    pinMode(pwm_pin, OUTPUT);
    pinMode(direction_pin, OUTPUT);
    digitalWrite(pwm_pin, LOW);
    digitalWrite(direction_pin, LOW);
}

void Wheel::set_power(float value)
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
            analogWrite(pwm_pin, int(value * 255));
            digitalWrite(direction_pin, LOW);
            sign = 1;
        }
        else if ( value < 0.f )
        {
            analogWrite(pwm_pin, int(value * 255));
            digitalWrite(direction_pin, HIGH);
            sign = 0;
        }
        else
        {
            digitalWrite(pwm_pin, LOW);
            digitalWrite(direction_pin, LOW);
        }
    }
}


void Wheel::update()
{
    long speed = get_speed();
    error = speed - abs(abs_speed);

    if ( speed_control )
    {  
        pid.Compute();
        if (info_period.is_ready()){
            Serial.print("a_s:"); Serial.print(abs_speed);
            Serial.print(" c_s:"); Serial.print(speed);
            Serial.print(" error:");
            Serial.print(error);
            Serial.print(" pid_power:");
            Serial.print(pid_power);
            Serial.print("\n");
        }
        float cur_power;
        if (abs_speed > 0){
            cur_power = power + pid_power;

            if (cur_power <= 0.)
                cur_power = 0.;
        }else{
            cur_power = power - pid_power;

            if (cur_power > 0.)
                cur_power = 0.;
        }
        
        set_power(cur_power);
    }
}

