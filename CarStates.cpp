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
    power_offset(0.),
    dt(10000),
    time_before(micros()),
    param_angle(0),
    cur_count(0),
    common_count(0),
    stable_window(0),
    error_window(PI / 180.f * 10.f),
    first(true)
{
    myPID.SetOutputLimits(-1, 1);
}

void TurnAngleState::set_params(float p, float i, float d)
{
    myPID.SetTunings(p, i, d);
}

void TurnAngleState::set_offset(float offset)
{
    if (car.debug){
        Serial.print("set_offset: ");
        Serial.println(offset);
    }
    power_offset = offset;
}

void TurnAngleState::start(void * param)
{
    StartParams * s_params((StartParams *)param);

    //возвратим результат установки угла если поворот не был завершон
    if (s_params->angle != 0.0){
        if (first == false && cur_count < common_count + stable_window) {
            Serial.println("Reset complete");
            send_resp(get_error(car.giro_angles[0], start_angle));
        }
        first = false;
    }

    //распечатаем значения.
    if (car.debug){
        Serial.print("\nangle: ");
        Serial.print(s_params->angle);
        Serial.print("\nspeed: ");
        Serial.println(s_params->angle_speed);
    }

    start_angle = car.giro_angles[0];
    param_angle = s_params->angle;
    float dest_angle = start_angle  + param_angle;

    //рассчитаем шаг угла и количество итераций.
    float error = get_error(start_angle, dest_angle);
    float time = abs(error) / s_params->angle_speed;
    
    if (error != 0.0 && time * 1000000 >= dt) {
        common_count = (unsigned long)(time / (dt / 1000000.) );
        angle_step = error / common_count;
    }else{
        common_count = 0;
        angle_step = 0.0;
    }

    cur_count = 0; 
    time_before = micros();
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

void TurnAngleState::send_resp(float angle){
    CmdResponce resp = {Car::SetAngle, angle};
    Serial.write(0);
    Serial.write(sizeof(CmdResponce));
    Serial.write((const uint8_t *)&resp, sizeof(CmdResponce));
}

State::ProcessState TurnAngleState::process()
{
    if (!is_active)
        return Failed;

    unsigned long cur_time = micros();
    unsigned long cur_dt = cur_time - time_before;
    
    //ещё рано
    if (cur_dt < dt)
        return InProgress;
    
    //откатим время
    time_before = cur_time - cur_dt % dt;
    
    
    if (cur_time - time_before )
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
    if (param_angle != 0.0 && cur_count == common_count + stable_window){
        Serial.println("Good complete");
        send_resp(get_error(car.giro_angles[0], start_angle));
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
