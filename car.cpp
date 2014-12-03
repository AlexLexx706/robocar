#include "car.h"
#include <Wire.h>
#include <I2Cdev.h>
#include "Wheel.h"
#include "CarStates.h"
#include <Arduino.h>

Car::Car():
    ud_start_time(millis()),
    wheel_left(LEFT_WHEEL_PWM_PIN, LEFT_WHEEL_DIRECTION_PIN),
    wheel_right(RIGTH_WHEEL_PWM_PIN, RIGTH_WHEEL_DIRECTION_PIN),
    last_cmd_time(0),
    enable_walk(false),
    debug(true),
    info_period(0xffffffff),
    update_count(0),
    control_period(1000000),
    update_period(1000000)
{ 
    move_forward_state = new MoveForwardState(*this, 0.6, 15.f);
    turn_state = new TurnState(*this,  500000, 15.f, 0.4);
    move_back_state = new MoveBackState(*this, 800000, 0.6);
    turn_angle_state = new TurnAngleState(*this, PI/180. * 160., PI/180. * 4, 0.45, 0.3);
    //turn_angle_state = new TurnAngleState(*this, PI/180. * 120., PI/180. * 4, 1, 0.5);
   
    cur_state = move_forward_state;
    giro_angles[0] = 0.f;
    giro_angles[1] = 0.f;
    giro_angles[2] = 0.f;
}

void Car::init(){
    servo1.setMinimumPulse(700);
    servo1.setMaximumPulse(2550);

    servo2.setMinimumPulse(700);
    servo2.setMaximumPulse(2550);

    servo1.attach(9);
    servo2.attach(10);

    servo1.write(98);
    servo2.write(68);
    
    //инициализация ультрасоника
    us_int1.init(US_TRIGER_PIN);
}

Car::~Car()
{
    delete move_forward_state;
    delete turn_state;
    delete move_back_state;
}


void Car::EmitState(){
    InfoData data;
    data.giro_angles[0] = giro_angles[0];
    data.giro_angles[1] = giro_angles[1];
    data.giro_angles[2] = giro_angles[2];

    data.acell[0] = acell[0];
    data.acell[1] = acell[1];
    data.acell[2] = acell[2];

    data.distance_cm = us_int1.get_distance();
 
    data.left_wheel_spped = wheel_left.get_speed();
    data.right_wheel_spped = wheel_right.get_speed();
    
    data.left_wheel_count = wheel_left.get_count();
    data.right_wheel_count = wheel_right.get_count();
    
    data.servo_angle1_1 = servo1.read();
    data.servo_angle1_2 = servo2.read();
    
    Serial.write(0);
    Serial.write(sizeof(data) + 1);
    Serial.write(AccInfo);
    Serial.write((const uint8_t *)&data, sizeof(data));
}

void Car::update()
{
    wheel_left.update();
    wheel_right.update();

    //обновление дальномера
    us_int1.update();

    //вещаем состояние.
    if (info_period.is_ready()){
        EmitState();
    }
    
//    if (debug){
//        update_count++;
//        
//        if (update_period.isReady()){
//            Serial.print("update_count: ");
//            Serial.println(update_count);
//            update_count = 0;
//        }
//    }
    

    //алгоритм обхода препятствий.
    if ( enable_walk )
    {
        State::ProcessState res = cur_state->process();

        //cостояние не изменилось
        if (res == State::InProgress)
            return;
        
        //1. Двигали в перёд.        
        if (cur_state->get_type() == State::MoveForward )
        {
            //поворот на лево
            if (debug)
                Serial.println("start turn left");

            cur_state = turn_state;
            TurnState::Direction dir(TurnState::Left);
            cur_state->start(&dir);
        }
        //2. поворачивали.
        else if (cur_state->get_type() == State::Turn)
        {
            //всё ок Двигаем дальше.
            if ( res == State::Ok )
            {
                if (debug)
                    Serial.println("start move forward");

                cur_state = move_forward_state;
                cur_state->start(0);
            }
            //поворот не удался.
            else
            {
                //поверён на право
                if ( ((TurnState *)cur_state)->get_direction() == TurnState::Left )
                {
                    if (debug)
                        Serial.println("start turn right");

                    cur_state = turn_state;
                    TurnState::Direction dir(TurnState::Right);
                    cur_state->start(&dir);
                }
                //отедим на зад.
                else
                {
                    if (debug)
                        Serial.println("start move back");

                    cur_state = move_back_state;
                    cur_state->start(0);
                }
            }
        }
        //Двигали на задад
        else if (cur_state->get_type() == State::MoveBack)
        {
            if (debug)
                Serial.println("MoveBack before turn left");
    
            //поворачиваем на лево.
            cur_state = turn_state;

            TurnState::Direction dir(TurnState::Left);
            cur_state->start(&dir);
        }/**
        else if (cur_state->get_type() == State::TurnAngle)
        {
            cur_state = turn_angle_state;
            float angle(0.0);
            cur_state->start(&angle);
        }**/
    //потеря связи с оператором
    }
    /*
    else if (control_period.isReady())
    {
        wheel_left.set_power(0.f);
        wheel_right.set_power(0.f);

        //if (debug){
        //    Serial.println("control_period estimate");
        //}
    }
    **/
}

void Car::process_command(uint8_t * data, uint8_t data_size)
{
    if (data_size == 0)
        return;

    //левое колесо
    if ( data[0] == SetLeftWheelPower && data_size >= 5 )
    {
        wheel_left.set_power(*((float *)&data[1]));
        wheel_left.speed_control = false;
        enable_walk = false;
        control_period.reset();

        if (debug) {
            Serial.print("left_power: ");
            Serial.print(*((float *)&data[1]));
            Serial.print("\n");
        }
    }
    //правое колесо
    else if ( data[0] == SetRightWheelPower  && data_size >= 5 )
    {
        wheel_right.set_power(*((float *)&data[1]));
        wheel_right.speed_control = false;
        enable_walk = false;
        control_period.reset();

        if (debug) {
            Serial.print("right_power: ");
            Serial.print(*((float *)&data[1]));
            Serial.print("\n");
        }
    }
    //оба колеса.
    else if ( data[0] == SetWheelsPower  && data_size >= 9 )
    {
        float l = *((float *)&data[1]);
        float r = *((float *)&data[5]);
        wheel_left.set_power(l);
        wheel_right.set_power(r);
        enable_walk = false;
        wheel_right.speed_control = false;
        wheel_left.speed_control = false;
        control_period.reset();
    }
    //остановка.
    else if ( data[0] == SetPowerZerro )
    {
        wheel_left.set_power(0.f);
        wheel_right.set_power(0.f);
        wheel_right.speed_control = false;
        wheel_left.speed_control = false;
        enable_walk = false;
        control_period.reset();
    }
    //запуск исследования
    else if ( data[0] == StartWalk )
    {
        cur_state = move_forward_state;
        cur_state->start(0);
        enable_walk = true;
    }
    //установка пидов
    else if ( data[0] == SetPidSettings )
    {
        struct Params{
          byte id;
          float p,i,d;
        } * params((Params *)&data[1]);

        if (debug){
            Serial.print("SetPidSettings id:");
            Serial.print(params->id);
            Serial.print(" p:");
            Serial.print(params->p);
            Serial.print(" i:");
            Serial.print(params->i);
            Serial.print(" d:");
            Serial.print(params->d);
            Serial.print("\n");
        }

        //установка пида угла
        if (params->id == 0){
            ((TurnAngleState *)turn_angle_state)->set_params(params->p, params->i, params->d);
        //установка пида левого колеса
        }else if (params->id == 1){
            wheel_left.pid.SetTunings(params->p, params->i, params->d);
            wheel_left.speed_control = true;
        //установка пида правого колеса
        }else if (params->id == 2){
            wheel_right.pid.SetTunings(params->p, params->i, params->d);
            wheel_right.speed_control = true;
        }
    }
    //установка ориентации
    else if ( data[0] == SetAngle )
    {
        
        TurnAngleState::StartParams * s_p((TurnAngleState::StartParams *)&data[1]);
        cur_state = turn_angle_state;
        cur_state->start(s_p);
        enable_walk = true;
    }
    //установка смещения
    else if ( data[0] == SetPowerOffset )
    {
        //установка в состояние перемещение.
        if (cur_state != turn_angle_state)
        {
            TurnAngleState::StartParams s_p;

            s_p.angle = 0.;
            s_p.angle_speed = PI / 180.f * 90.f;
            turn_angle_state->start(&s_p);
        }

        cur_state = turn_angle_state;
        enable_walk = true;
        ((TurnAngleState *)turn_angle_state)->set_offset(*((float *)&data[1]));
    }
    //разрешить режим отладки
    else if ( data[0] == EnableDebug ){
       debug = (bool)data[1];
    }
    //установка скоро
    else if ( data[0] == SetWheelSpeed )
    {
        struct Params{
          byte id;
          int speed;
        } * params((Params *)&data[1]);

        if (debug){
            Serial.print("SetWheelSpeed id:");
            Serial.print(params->id);
            Serial.print(" speed:");
            Serial.print(params->speed);
            Serial.print("\n");
        }

        if (params->id == 0){
            wheel_left.set_abs_speed(params->speed);
            wheel_left.speed_control = true;
        //установка пида правого колеса
        }else if (params->id == 1){
            wheel_right.set_abs_speed(params->speed);
            wheel_right.speed_control = true;
        }
        else{
            wheel_left.set_abs_speed(params->speed);
            wheel_right.set_abs_speed(params->speed);
            wheel_right.speed_control = true;
            wheel_left.speed_control = true;        
        }
    }
    else if ( data[0] == SetServoAngle )
    {
        struct Params{
          byte id;
          unsigned char angle;
        } * params((Params *)&data[1]);

        if (debug){
            Serial.print("SetServoAngle id:");
            Serial.print(params->id);
            Serial.print(" angle:");
            Serial.println(params->angle);
        }

        if (params->id == 0){
            servo1.write(params->angle);
        //установка пида правого колеса
        }else if (params->id == 1){
            servo2.write(params->angle);
        }else{
            if (debug){
                Serial.print("Wrong servo number:");
                Serial.println(params->id);
            }
        }
    }
    //включить вещание состояния
    else if ( data[0] == SetInfoPeriod ){
        unsigned long * period((unsigned long *)&data[1]);
        
        if (debug){
            Serial.print("SetInfoPeriod period:");
            Serial.println(*period);
        }
        
        info_period.set_period(*period);
    }
}

