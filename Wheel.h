#ifndef _WHEEL_SPEED_H_
#define _WHEEL_SPEED_H_
#include <Arduino.h>
#include "my_pid.h"
#include "period.h"

#define MIN_UPDATE_COUNT_PERIOD_MKS 12500

class Wheel
{
public:
    Wheel(int pwm_pin, int direction_pin);
    void update();
    void set_abs_speed(long speed){abs_speed = speed;};
    long get_abs_speed() const {return abs_speed;};

    long get_speed() const {return speed;}
    
    long get_count() const {
        long res;
        noInterrupts();
        res = count;
	interrupts();
	return res;
    }

    void set_power(float value);
    float get_power() const {return power;}
    void set_speed_control(bool enable){speed_control = enable;};
    bool is_speed_control() const {return speed_control;};

    inline void updata_count() { 
        unsigned long ct = micros();
        
        //ложное срабатывание
        if ((ct - cur_time) < MIN_UPDATE_COUNT_PERIOD_MKS){
            cur_time = ct;
            return;
        }

        if (sign)
            count++;
        else
            count--;

        speed = ct - cur_time;
        cur_time = ct;
    }

    PID pid;
    bool speed_control;
private:
    long count;
    long speed;
    unsigned long cur_time;
    int pwm_pin;
    int direction_pin;
    float power;
    int abs_speed;
    float pid_power;
    float error;
    Period info_period;
    byte sign;

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
