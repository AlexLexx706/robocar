#include "car.h"
#include <Wire.h>
#include <I2Cdev.h>
#include "Wheel.h"
#include "CarStates.h"
#include <Arduino.h>

Car::Car():
    ud_start_time(millis()),
    distance_cm(0.f),
    wheel_left(4, 3, 5),
    wheel_right(A1, 6, 9),
    ultrasonic(7, 8),
    last_cmd_time(0),
    check_last_time(false),
    enable_walk(false),
    max_walk_power(0.5),
    min_distance(20)
{ 
    move_forward_state = new MoveForwardState(*this, 0.4, 15.f);
    turn_state = new TurnState(*this,  800000, 15.f, 0.3);
    move_back_state = new MoveBackState(*this, 800000, 0.3);
    cur_state = move_forward_state;
}

Car::~Car()
{
    delete move_forward_state;
    delete turn_state;
    delete move_back_state;
}


void Car::update()
{
    wheel_left.update();
    wheel_right.update();
    update_distance();
    
    //потерянна связь с оператором.
    if (check_last_time && (micros() > last_cmd_time + 100000) )
    {
        //остановка машины.
        wheel_left.set_power(0.f);
        wheel_right.set_power(0.f);
        check_last_time = false;
    }
    //алгоритм обхода препятствий.
    else if ( enable_walk )
    {
        State::ProcessState res = cur_state->process();

        //cостояние не изменилось
        if (res == State::InProgress)
            return;
        
        //переход к следующему состоянию
        //Serial.print("res:");
        //Serial.println(res);

        //1. Двигали в перёд.        
        if (cur_state->get_type() == State::MoveForward )
        {
            //поворот на лево
            //Serial.println("start turn left");
            cur_state = turn_state;
            TurnState::Direction dir(TurnState::Left);
            cur_state->start(&dir);
        }
        //2. поворачивали.
        else if (cur_state->get_type() == State::Turn)
        {
            //Serial.println("turn before");

            //всё ок Двигаем дальше.
            if ( res == State::Ok )
            {
                //Serial.println("start move forward");
                cur_state = move_forward_state;
                cur_state->start(0);
            }
            //поворот не удался.
            else
            {
                //поверён на право
                if ( ((TurnState *)cur_state)->get_direction() == TurnState::Left )
                {
                    //Serial.println("start turn right");
                    cur_state = turn_state;
                    TurnState::Direction dir(TurnState::Right);
                    cur_state->start(&dir);
                }
                //отедим на зад.
                else
                {
                    //Serial.println("start move back");
                    cur_state = move_back_state;
                    cur_state->start(0);
                }
            }
        }
        //Двигали на задад
        else if (cur_state->get_type() == State::MoveBack)
        {
            //Serial.println("MoveBack before turn left");
            //поворачиваем на лево.
            cur_state = turn_state;

            TurnState::Direction dir(TurnState::Left);
            cur_state->start(&dir);
        }
    }
} 

void Car::process_command(uint8_t * data, uint8_t data_size)
{
    if (data_size == 0)
        return;

    //левое колесо
    if ( data[0] == SetLeftWheelPower && data_size >= 5 )
    {
        wheel_left.set_power(*((float *)&data[1]));
        enable_walk = false;
    }
    //правое колесо
    else if ( data[0] == SetRightWheelPower  && data_size >= 5 )
    {
        wheel_right.set_power(*((float *)&data[1]));
        enable_walk = false;
    }
    //оба колеса.
    else if ( data[0] == SetWheelsPower  && data_size >= 9 )
    {
        float l = *((float *)&data[1]);
        float r = *((float *)&data[5]);
        wheel_left.set_power(l);
        wheel_right.set_power(r);
        enable_walk = false;
    }
    //остановка.
    else if ( data[0] == SetPowerZerro )
    {
        wheel_left.set_power(0.f);
        wheel_right.set_power(0.f);
        enable_walk = false;
    }
    else if ( data[0] == StartWalk )
    {
        cur_state = move_forward_state;
        cur_state->start(0);
        enable_walk = true;
        Serial.println("enable_walk");
    }

    //Запрос времени комманды.
    if ( !enable_walk )
    {
        last_cmd_time = micros();
        check_last_time = true;
    }
}



void Car::update_distance()
{
    if ( millis() > ud_start_time + 100 )
    {       
        distance_cm = ultrasonic.Ranging(CM);
        ud_start_time = millis();
    }
}
