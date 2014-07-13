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
    angle(0.f),
    set_point(0.f),
    error(0.f),
    power(0.f),
    myPID(&error, &power, &set_point, 1.1, 0.5, 0.1, DIRECT)
    //myPID(&error, &power, &angle, 0, 0, 0, DIRECT)
{
    myPID.SetOutputLimits(-0.7, 0.7);
    myPID.SetSampleTime(10);
    direction[0] = 0.f;
    direction[1] = 1.f;
    myPID.SetMode(AUTOMATIC);
}

void TurnAngleState::set_params(float p, float i, float d)
{
    Serial.print("p:");
    Serial.print(p, 4);
    Serial.print(" i:");
    Serial.print(i, 4);
    Serial.print(" d:");
    Serial.print(d, 4);
    Serial.println("");
    
    myPID.SetTunings(p, i, d);
}

void TurnAngleState::set_angle(float c_angle)
{
    Serial.print("angle:");
    Serial.print(c_angle, 4);
    Serial.println("");
    
    angle = c_angle;
    direction[0] = cos(angle);
    direction[1] = sin(angle);
}



void TurnAngleState::start(void * param)
{
    //установим угол.
    if (param)
        set_angle(*((float *)(param)));

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
    error = get_direction();
    myPID.Compute();
    
    Serial.print("c_a:");
    Serial.print(car.giro_angles[0], 4);
    
    Serial.print(" d_a:");
    Serial.print(angle, 4);

    Serial.print(" e_a:");
    Serial.print(error, 4);
    Serial.print(" p:");
    Serial.print(power, 4);
    Serial.print("\n");

    if (power >= 0 )
    {
        car.wheel_left.set_power(-power);
        car.wheel_right.set_power(power);
        return InProgress;
    }
    else
    {
        car.wheel_left.set_power(-power);
        car.wheel_right.set_power(power);
        return InProgress;
    }
}
