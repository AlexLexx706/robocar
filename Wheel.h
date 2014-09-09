#ifndef _WHEEL_SPEED_H_
#define _WHEEL_SPEED_H_
#include <Arduino.h>
#include "my_pid.h"
#include "period.h"

class Wheel
{
public:
    Wheel(int forward_pin, int backward_pin, int speed_counter_pin);
    void update();
    void set_abs_speed(int speed){abs_speed = speed;};
    unsigned long get_abs_speed() const {return abs_speed;};

    int get_speed() const {
	int res;
	uint8_t oldSREG = SREG;
	cli();
        res = speed;
	SREG = oldSREG;
	return res;
    }    
    void set_power(double value);
    double get_power() const {return power;}
    void set_speed_control(bool enable){speed_control = enable;};
    bool is_speed_control() const {return speed_control;};
    void updata_count();
    
       
    PID pid;
    bool speed_control;
private:
    volatile int count;
    volatile int speed_pin_state;
    volatile int speed;
    int forward_pin;
    int backward_pin;
    int speed_counter_pin;
    double power;
    unsigned long abs_speed;
    double pid_power;
    double error;
    Period info_period;
    Period count_period;

    int take_count() {
        int res;
        uint8_t SaveSREG = SREG;
        cli();                  
        res = count;            
        count = 0;
        SREG = SaveSREG;        
        return res;
    }
};

#endif
