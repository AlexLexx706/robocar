#ifndef ALEX_CAR_H
#define ALEX_CAR_H
#include <arduino.h>


class Car
{
public:
    enum Wheel{LeftWheel, RightWheel};
    static Car & instance();
    void update();
    void set_speed(Wheel wheel, float value);    
    
private:
    float l_speed;
    float r_speed;
    float heading;
    unsigned long start_time;
    float dist_cm;
    float direction[2];

    Car();
};

#endif
