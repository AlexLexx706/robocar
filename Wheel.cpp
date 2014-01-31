#include "Wheel.h"

Wheel::Wheel(int __speed_pin, int __forward_pin, int __backward_pin)
{
    counter = 0;
    speed_pin = __speed_pin;
    forward_pin = __forward_pin;
    backward_pin = __backward_pin;
    speed_list_index = 0;;
    cur_speed = 0.;
    abs_speed = 0.;

    pinMode(speed_pin, INPUT);
    pinMode(forward_pin, OUTPUT);
    pinMode(backward_pin, OUTPUT);
    digitalWrite(backward_pin, LOW);
    digitalWrite(forward_pin, LOW);

    state = digitalRead(speed_pin);
    start_time = micros();
    power = 0.f;

    for (int i = 0; i < sizeof(speed_list)/sizeof(speed_list[0]); i++ )
    {
        speed_list[i] = 0.;
    }
}


void Wheel::set_power(float value)
{
    if (value > 1.f )
        value = 1.f;
    else if (value < -1.0)
        value = -1.0;

    if (value != power )
    {
        power = value;

        if ( value > 0.f )
        {
            analogWrite(forward_pin, int(value * 255));
            digitalWrite(backward_pin, LOW);
        }
        else if ( value < 0.f )
        {
            analogWrite(backward_pin, int(-(value * 255)));
            digitalWrite(forward_pin, LOW);
        }
    }
}


void Wheel::update()
{
    update_speed_value();
    
//    if ( get_speed() > get_abs_speed() )
//       set_power(get_power() - 0.001);
//    else
//       set_power(get_power() + 0.001);
}


void Wheel::update_speed_value()
{
    int cur_state = digitalRead(speed_pin);
    unsigned long cur_time = micros();

    if ( state != cur_state )
    {
        if ( state == HIGH && cur_state == LOW )
        {
            counter++;
            
            //рассчёт скорости
            unsigned long dt = cur_time - start_time;
            start_time = cur_time;
             
            speed_list[speed_list_index] = 1000000./dt;
            speed_list_index++;
            speed_list_index %= (sizeof(speed_list)/sizeof(speed_list[0]));
            
            cur_speed = 0.f;
            
            for (int i = 0; i < sizeof(speed_list)/sizeof(speed_list[0]); i++ )
               cur_speed += speed_list[i];
          
            cur_speed = cur_speed / (sizeof(speed_list)/sizeof(speed_list[0]));
        }
        
        state = cur_state;
    }
    
    //считаем что скорость 0
    if (cur_time > start_time + 100000 )
    {
        speed_list[speed_list_index] = 0;
        start_time = cur_time;

        speed_list_index++;
        speed_list_index %= (sizeof(speed_list)/sizeof(speed_list[0]));
        
        cur_speed = 0.f;
        
        for (int i = 0; i < sizeof(speed_list)/sizeof(speed_list[0]); i++ )
           cur_speed += speed_list[i];
      
        cur_speed = cur_speed / (sizeof(speed_list)/sizeof(speed_list[0]));
    }
}


