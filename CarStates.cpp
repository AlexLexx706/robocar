#include "CarStates.h"
#include "car.h"
#include "vectoper.h"

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

///////////////////////////////////////////////////////////////////////////////////
TurnAngleState::TurnAngleState(Car & car, float _max_window,  float _min_window, float _max_power, float _min_power):
    State(car, State::TurnAngle),
    max_window(_max_window),
    min_window(_min_window),
    max_power(_max_power),
    min_power(_min_power)
{
    direction[0] = 1.f;
    direction[0] = 1.f;
}
void TurnAngleState::start(void * param)
{
    //установим угол.
    if (param)
    {
        direction[0] = cos(*((float *)(param)));
        direction[1] = sin(*((float *)(param)));
    }

    car.wheel_left.set_power(0);
    car.wheel_right.set_power(0);
    State::start(param);
}

float TurnAngleState::get_direction()
{
    float cur_direction[2] = {cos(double(car.giro_angles[0])), sin(double(car.giro_angles[0]))};
    float perp_direction[2] = {-cur_direction[1], cur_direction[0]};
    float angle = acos(ad_vo_scalprod(2, cur_direction, direction));

    //поворот на право
    if (ad_vo_scalprod(2, perp_direction, direction) < 0)
        return -angle;
    //поворот на лево
    return angle;
}


State::ProcessState TurnAngleState::process()
{
    if (!is_active)
        return Failed;
    
    //рассчёт угла и направления поворота.
    float angle = get_direction();
    float abs_angle = abs(angle);

    
    if ( abs_angle <= min_window )
    {
        car.wheel_left.set_power(0);
        car.wheel_right.set_power(0);
        return Ok;
    }
    else
    {
        Serial.print("max:");
        Serial.print(max_window);
        Serial.print(" min:");
        Serial.print(min_window);
        
        float cur_power = max_power;

        if ( abs_angle < max_window )
        {
            cur_power = max_power - (max_power - min_power) * (1.f - (abs_angle - min_window)/(max_window - min_window));
        }
        Serial.print("cur_power:");
        Serial.println(cur_power);
        
        //поворот на лево
        if (angle > 0 )
        {
            car.wheel_left.set_power(cur_power);
            car.wheel_right.set_power(-cur_power);
            return InProgress;
        }
        else
        {
            car.wheel_left.set_power(-cur_power);
            car.wheel_right.set_power(cur_power);
            return InProgress;
        }
    }
}
