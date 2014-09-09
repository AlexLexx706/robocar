#include "Wheel.h"

#define MAX_COUNT 1500

Wheel::Wheel(int __forward_pin, int __backward_pin, int __speed_counter_pin):
    speed(0),
    pid(&error, &pid_power, 2, 0, 0.35),
    speed_control(false),
    forward_pin(__forward_pin),
    backward_pin(__backward_pin),
    speed_counter_pin(__speed_counter_pin),
    power(0.0),
    abs_speed(30),
    pid_power(0.0),
    error(0.0),
    info_period(100000),
    count(0),
    count_period(1000000)
{
    pid.SetOutputLimits(0,1);
    pinMode(forward_pin, OUTPUT);
    pinMode(backward_pin, OUTPUT);
    digitalWrite(backward_pin, LOW);
    digitalWrite(forward_pin, LOW);
    
    //прочитаем состояние пина
    pinMode(speed_counter_pin, INPUT);
    speed_pin_state = digitalRead(speed_counter_pin);
}

void Wheel::updata_count(){
    int cs = digitalRead(speed_counter_pin);

    //есть изменение, начало счёта 
    if (cs != speed_pin_state){
        speed_pin_state = cs;
        speed = count;
        count = 0;
    //счетаем
    }else{
        count++;

        //состояние долго не меняется достигли максимума
        if (count >= MAX_COUNT){
            count = MAX_COUNT;
            speed = count;
        }
    }
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
    unsigned long speed = get_speed();
    error = abs_speed - speed;

    if ( speed_control )
    {  
        pid.Compute();
        if (info_period.isReady()){
            Serial.print("a_s:"); Serial.print(abs_speed);
            Serial.print(" c_s:"); Serial.print(speed);
            Serial.print(" error:");
            Serial.print(error);
            Serial.print(" power:");
            Serial.print(pid_power);
            Serial.print("\n");
        }
        set_power(pid_power);
    }
}

