#ifndef ALEX_CAR_H
#define ALEX_CAR_H
#include "Wheel.h"
#include "Ultrasonic.h"
#include "my_pid.h"
#include "period.h"

//номера пинов
#define US_TRIGER_PIN 7
#define US_ECHO_PIN 8
#define US_TRIGER_TIMEOUT_MK 50000
#define US_MAX_DURATION_MK 500000

#define LEFT_WHEEL_PWM_PIN 5
#define LEFT_WHEEL_DIRECTION_PIN 3

#define RIGTH_WHEEL_PWM_PIN 6
#define RIGTH_WHEEL_DIRECTION_PIN 9

#define LEFT_WHEEL_SPEED_COUNTER_PIN 4
#define RIGHT_WHEEL_SPEED_COUNTER_PIN 10

class State;

class Car
{
public:
    //комманды.
    enum CmdType{SetLeftWheelPower = 0,
                 SetRightWheelPower,
                 SetWheelsPower,
                 SetPowerZerro,
                 StartWalk,
                 SetPidSettings,
                 SetAngle,
                 EnableDebug,
                 SetPowerOffset,
                 SetWheelSpeed};

    Car();
    ~Car();
    void update();
    Wheel wheel_left;
    Wheel wheel_right;
    void process_command(uint8_t * data, uint8_t data_size);
    float get_distance() const {return distance_cm;}
    void start_walk();
    void start_rotate(float angle);
    float giro_angles[3];
    bool show_info;

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
    Period info_period;
 
    void update_distance();
};

void setup_dmp6();
void update_dmp6(float euler[3]);

#endif
