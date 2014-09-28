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
    car.wheel_left.set_power(max_power);
    car.wheel_right.set_power(max_power);
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
        car.wheel_left.set_power(-max_power);
        car.wheel_right.set_power(max_power);
    }
    //поворот на право
    else
    {
        car.wheel_left.set_power(max_power);
        car.wheel_right.set_power(-max_power);
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
    car.wheel_left.set_power(-max_power);
    car.wheel_right.set_power(-max_power);
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
    set_point(0.f),
    error(0.f),
    power(0.f),
    myPID(&error, &power, 2, 0, 0.35),
    power_offset(0.)
    
{
    myPID.SetOutputLimits(-1, 1);
}

void TurnAngleState::set_params(float p, float i, float d)
{
    myPID.SetTunings(p, i, d);
}

void TurnAngleState::set_offset(float offset)
{
    power_offset = offset;
}

void TurnAngleState::start(void * param)
{
    StartParams * s_params((StartParams *)param);

    //использовать абсолютный угол
    myPID.Reset();

    start_angle = car.giro_angles[0];
    float dest_angle;

    if (s_params->use_abs_angle){
        dest_angle = s_params->angle;
    //относителный угол
    }else{
        dest_angle = start_angle  + s_params->angle;
    }

    //рассчитаем шаг угла и количество итераций.
    float error = get_error(start_angle, dest_angle);
    float time = abs(error) / s_params->angle_speed;
    common_count = (unsigned long)(time / 0.01);
    cur_count = 0;
    angle_step = error / common_count;
    stable_window = 100;
    error_window = PI / 180.f * 10.f;
    
    //распечатаем значения.
    if (car.debug){
        Serial.print("use_abs_angle: ");
        Serial.print(s_params->use_abs_angle);
        Serial.print("\nstart_angle: ");
        Serial.print(start_angle);
        Serial.print("\ndest_angle: ");
        Serial.print(dest_angle);
        Serial.print("\nerror: ");
        Serial.print(error);
        Serial.print("\nspeed: ");
        Serial.print(s_params->angle_speed);
        Serial.print("\ncommon_count: ");
        Serial.print(common_count);
        Serial.print("\n");
    }

    car.wheel_left.set_power(0);
    car.wheel_right.set_power(0);
    State::start(param);
}

float TurnAngleState::get_error(float start, float end)
{
    float direction[2] = {cos(end), sin(end)};
    float cur_direction[2] = {cos(start), sin(start)};
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
    cur_count++;
    float angle;

    //изменеение угла
    if (cur_count <= common_count){
        angle = start_angle + angle_step * cur_count;
    }else {
        angle = start_angle + angle_step * common_count;
    }
    
    error = get_error(car.giro_angles[0], angle);
   
    //проверка завершения
    if (cur_count == common_count + stable_window){
        car.wheel_left.set_power(0);
        car.wheel_right.set_power(0);
        is_active = false;

        //всё ок уложились в окно
        if (abs(error) <= error_window){
            if (car.debug){
                Serial.print("error: ");
                Serial.print(error);
                Serial.print("\n Turn OK\n");
            }
            return Ok;
        }
        if (car.debug){
            Serial.print("error: ");
            Serial.print(error);
            Serial.print("\n Turn Failed\n");
        }
        return Failed;
    }

    myPID.Compute();

    if (power >= 0 )
    {
        car.wheel_left.set_power(-power + power_offset);
        car.wheel_right.set_power(power + power_offset);
    }
    else
    {
        car.wheel_left.set_power(-power + power_offset);
        car.wheel_right.set_power(power + power_offset);
    }
    return InProgress;
}
