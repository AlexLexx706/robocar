#ifndef _WHEEL_SPEED_H_
#define _WHEEL_SPEED_H_
#include <Arduino.h>
#include "my_pid.h"

class Wheel
{
public:
    Wheel(int forward_pin, int backward_pin);
    void update();
    void set_abs_speed(int speed){
      if ( speed > min_speed )
          abs_speed = min_speed;
      else if ( speed < max_speed )
          abs_speed = max_speed;
      else
        abs_speed = speed;
    };
    int get_abs_speed() const {return abs_speed;};

    void set_power(double value);
    double get_power() const {return power;}
    void set_speed_control(bool enable){speed_control = enable;};
    bool is_speed_control() const {return speed_control;};

    int get_speed(){
        int res;
        uint8_t SaveSREG = SREG;// save interrupt flag
        cli();                  // disable interrupts
        res = speed;            // access the shared data
        SREG = SaveSREG;         // restore the interrupt flag
        return res;
    }

    void set_speed(int value){
        uint8_t SaveSREG = SREG; // save interrupt flag
        cli();                   // disable interrupts
        speed = value;           // access the shared data
        SREG = SaveSREG;         // restore the interrupt flag
    }

    unsigned long get_last_time(){
        unsigned long res;
        uint8_t SaveSREG = SREG;// save interrupt flag
        cli();                  // disable interrupts
        res = last_time;        // access the shared data
        SREG = SaveSREG;         // restore the interrupt flag
        return res;
    }

    static const int max_speed;
    static const int min_speed;
    volatile int speed;
    volatile unsigned long last_time;
    PID pid;
    bool speed_control;
private:
    int forward_pin;
    int backward_pin;
    double power;
    int abs_speed;
    double pid_power;
    double error;

    void update_speed_value();
};

#endif
