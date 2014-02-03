#include "CarStates.h"
#include "car.h"

MoveForwardState::MoveForwardState(Car & car, float _max_power, float _min_distance):
  State(car, State::MoveForward),
  max_power(_max_power),
  min_distance(_min_distance)
{}

void MoveForwardState::start(void * param)
{
    car.wheel_left.set_power(-max_power);
    car.wheel_right.set_power(-max_power);
    State::start(param);
}

State::ProcessState MoveForwardState::process()
{
    if (!is_active)
    {
        car.wheel_left.set_power(0);
        car.wheel_right.set_power(0);
        return Failed;
    }
    
    //делаем левый поворот.
    if ( car.get_distance() >  min_distance )
        return InProgress;

    car.wheel_left.set_power(0);
    car.wheel_right.set_power(0);
    is_active = false;

    return Failed;
}

////////////////////////////////////////////////////////////////////////////////////////////////////////
TurnState::TurnState(Car & car, unsigned long _max_turn_time, float _min_distance, float _max_power):
    State(car, Turn),
    max_turn_time(_max_turn_time),
    start_time(0),
    dir(TurnState::Left),
    min_distance(_min_distance),
    max_power(_max_power)
{}

void TurnState::start(void * param)
{
    if ( param)
        dir = *((TurnState::Direction *)(param));

    //поворот на лево.
    if (dir == Left)
    {
        car.wheel_left.set_power(max_power);
        car.wheel_right.set_power(-max_power);
    }
    else
    {
        car.wheel_left.set_power(-max_power);
        car.wheel_right.set_power(max_power);
    }
    start_time = micros();
    State::start(param);
}

State::ProcessState TurnState::process()
{
    if (!is_active)
    {
        car.wheel_left.set_power(0);
        car.wheel_right.set_power(0);
        return Failed;
    }
    
    //всё ок продолжаем поворот.
    if (micros() < start_time + max_turn_time )
    {
        if (car.get_distance() < min_distance )
            return InProgress;
        return Ok;
    }

    is_active = false;
    car.wheel_left.set_power(0);
    car.wheel_right.set_power(0);
    return Failed;
}

////////////////////////////////////////////////////////////////////////////
MoveBackState::MoveBackState(Car & car, unsigned long _max_time, float _max_power):
  State(car, MoveBack),
  max_time(_max_time),
  max_power(_max_power)
{

}

void MoveBackState::start(void * param)
{
    start_time = micros();
    State::start(param);
    car.wheel_left.set_power(max_power);
    car.wheel_right.set_power(max_power);
}

State::ProcessState MoveBackState::process()
{
    if ( !is_active )
    {
        car.wheel_left.set_power(0);
        car.wheel_right.set_power(0);
        return Failed;
    }
    
    if ( micros() < start_time + max_time )
        return InProgress;

    car.wheel_left.set_power(0);
    car.wheel_right.set_power(0);
    return Ok;
}



