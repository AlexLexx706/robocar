#ifndef ALEX_CAR_H
#define ALEX_CAR_H

class Car
{
public:
    enum Wheel{LeftWheel, RightWheel};
    static Car & instance();
    void update();
    void set_speed(Wheel wheel, float value);    
    
private:
    unsigned long ud_start_time;
    float distance_cm;
    
    Car();
    void update_distance();
    
};

#endif
