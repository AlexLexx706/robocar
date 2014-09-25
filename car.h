#ifndef ALEX_CAR_H
#define ALEX_CAR_H
#include "Wheel.h"
#include <UltrasonicInt1.h>
#include "my_pid.h"
#include "period.h"
#include <ServoTimer1.h>
#include <helper_3dmath.h>

//номера пинов
#define US_TRIGER_PIN 7

#define US_TRIGER_TIMEOUT_MK 50000
#define US_MAX_DURATION_MK 500000

#define LEFT_WHEEL_PWM_PIN 5
#define LEFT_WHEEL_DIRECTION_PIN 8

#define RIGTH_WHEEL_PWM_PIN 6
#define RIGTH_WHEEL_DIRECTION_PIN A1

#define LEFT_WHEEL_SPEED_COUNTER_PIN 4
#define RIGHT_WHEEL_SPEED_COUNTER_PIN A0

class State;

class Car
{
    struct InfoData{ //описывает структуру состояния
        float giro_angles[3];
        float gravity[3];
        long distance_cm;
        unsigned short left_wheel_spped;
        unsigned short right_wheel_spped;
        uint8_t servo_angle1_1;
        uint8_t servo_angle1_2;
    };
    
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
                 SetWheelSpeed, 
                 SetServoAngle,
                 SetInfoPeriod,
                 AccInfo};

    Car();
    ~Car();
    void init();
    void update();
    Wheel wheel_left;
    Wheel wheel_right;
    void process_command(uint8_t * data, uint8_t data_size);
    long get_distance() const {return us_int1.get_distance();}
    void start_walk();
    void start_rotate(float angle);
    float giro_angles[3];
    VectorFloat gravity;
    bool debug;

private:
    unsigned long ud_start_time;
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

    ServoTimer1 servo1;
    ServoTimer1 servo2;
    int update_count;

    void EmitState();
};

void setup_dmp6();
void update_dmp6(float euler[3]);

#endif
