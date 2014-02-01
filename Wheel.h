#ifndef _WHEEL_SPEED_H_
#define _WHEEL_SPEED_H_
#include <arduino.h>

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
private:
    uint32_t counter;
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
    
    void update_speed_value();
};

#endif
