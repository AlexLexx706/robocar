#ifndef _WHEEL_SPEED_H_
#define _WHEEL_SPEED_H_
#include <Arduino.h>

class Wheel
{
public:
    Wheel(int speed_pin, int forward_pin, int backward_pin);
    void update();
    void set_abs_speed(float speed){abs_speed = speed;};
    float get_abs_speed() const {return abs_speed;};
    
    float get_speed() const {return cur_speed;};
    void set_power(float value);
    float get_power() const {return power;}
    void set_speed_control(bool enable){speed_control = enable;};
    bool is_speed_control() const {return speed_control;};
    uint8_t * counter;
    
private:
    int state;
    unsigned long start_time;
    float speed_list[3];
    uint8_t speed_list_index;
    float cur_speed;
    int speed_pin;
    int forward_pin;
    int backward_pin;
    float power;
    float abs_speed;
    bool speed_control;
    
    void update_speed_value();
};

#endif
