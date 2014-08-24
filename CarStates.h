#ifndef _CarState_H
#define _CarState_H
#include "my_pid.h"

class Car;
class PID;

class State
{
public:
    enum Type {MoveForward, Turn, MoveBack, TurnAngle};
    enum ProcessState {InProgress, Ok, Failed};

    State(Car & _car, Type _type):car(_car), type(_type),is_active(false){}
    virtual ~State(){}
    Type get_type() const {return type;}
    virtual void start(void * param){is_active = true;};
    virtual ProcessState process() = 0;
protected:
    Car & car;
    Type type;
    bool is_active;
};


//Двигать в перёд до препятствия
class MoveForwardState: public State
{
public:
    MoveForwardState(Car & car, float max_power, float min_distance);
    virtual void start(void * param);
    virtual ProcessState process();
private:
    float max_power;
    float min_distance;
};


//Поворачивать по времени.
class TurnState: public State
{
public:
    enum Direction {Left, Right};
    
    TurnState(Car & car, unsigned long max_turn_time, float min_distance, float max_power);
    virtual void start(void * param);
    virtual ProcessState process();
    Direction get_direction() const {return dir; }
    
private:
    unsigned long max_turn_time;
    unsigned long start_time;
    Direction dir;
    float min_distance;
    float max_power;
};


//Двигать назад по времени.
class MoveBackState: public State
{
public:
    MoveBackState(Car & car, unsigned long max_time, float max_power);
    virtual void start(void * param);
    virtual ProcessState process();
    
private:
    unsigned long max_time;
    unsigned long start_time;
    float max_power;
};

//Повернуться на угол
class TurnAngleState: public State
{
public:
    TurnAngleState(Car & car, float max_window,  float min_window, float max_power, float min_power);
    virtual void start(void * param);
    virtual ProcessState process();
    float get_direction();
    void set_params(float p, float i, float d);
    void set_angle(float angle);
    
    
private:
    float direction[2];
    double angle;
    double set_point;
    double error;
    double power;
    PID * myPID;
};





#endif
