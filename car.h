#ifndef ALEX_CAR_H
#define ALEX_CAR_H
#include "Wheel.h"
#include "Ultrasonic.h"

class State;

class Car
{
public:
    //комманды.
    enum CmdType{SetLeftWheelPower = 0, SetRightWheelPower, SetWheelsPower, SetPowerZerro, StartWalk, Test};

    Car();
    ~Car();
    void update();
    Wheel wheel_left;
    Wheel wheel_right;
    void process_command(uint8_t * data, uint8_t data_size);
    float get_distance() const {return distance_cm;}
    float giro_angles[3];

private:
    unsigned long ud_start_time;
    float distance_cm;
    Ultrasonic ultrasonic;
    unsigned long last_cmd_time;
    bool check_last_time;
    bool enable_walk;
    float max_walk_power;
    float min_distance;
    State * cur_state;
    State * move_forward_state;
    State * turn_state;
    State * move_back_state;
    State * turn_angle_state;
 
    void update_distance();
};

void setup_dmp6();
void update_dmp6(float euler[3]);

#endif
