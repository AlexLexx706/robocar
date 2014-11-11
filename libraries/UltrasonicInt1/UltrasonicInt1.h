#ifndef Ultrasonic_int_1_h
#define Ultrasonic_int_1_h

#include "Arduino.h"

class UltrasonicInt1
{
public:
    void init(int trig_pin, unsigned long max_distance=600);
    boolean update();
    long get_distance() const {return distance;}

private:
    int trig_pin;
    unsigned long max_duraion;
    long distance;
    unsigned long start_time;
    unsigned long duration;
    boolean ready;
    boolean complete;
    boolean wait_ready;
    
    
    friend void echo_falling();
};

extern UltrasonicInt1 us_int1;

#endif //#ifndef Ultrasonic_int_1_h
