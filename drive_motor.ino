#include "car.h"
#include "my_pid.h"
#include <PinChangeInt.h>
#include <ServoTimer1.h>
#include <UltrasonicInt1.h>

#include <I2Cdev.h>
#include <MPU6050.h>
#include <Wire.h>
#include <period.h>
#include "giro.h"

static Car car;
static Giro giro;
static Period giro_period(20000);
static uint8_t buffer[33];
static uint8_t buffer_size = 0;

void update_wheel_speed()
{
    if (PCintPort::arduinoPin == LEFT_WHEEL_SPEED_COUNTER_PIN)
        car.wheel_left.updata_count();
    else
        car.wheel_right.updata_count();
}

void setup() 
{ 
    Serial.begin(115200);
    Serial.println("Connect serial speed=115200!!!"); 
    giro.init();
    car.wheel_left.set_power(0);
    car.wheel_right.set_power(0);
    car.init();
    //инициализация подсчёта скорости     
    pinMode(LEFT_WHEEL_SPEED_COUNTER_PIN, INPUT); digitalWrite(LEFT_WHEEL_SPEED_COUNTER_PIN, HIGH);
    PCintPort::attachInterrupt(LEFT_WHEEL_SPEED_COUNTER_PIN, &update_wheel_speed, FALLING);
    pinMode(RIGHT_WHEEL_SPEED_COUNTER_PIN, INPUT); digitalWrite(RIGHT_WHEEL_SPEED_COUNTER_PIN, HIGH);
    PCintPort::attachInterrupt(RIGHT_WHEEL_SPEED_COUNTER_PIN, &update_wheel_speed, FALLING);
}

void loop() 
{
    if (giro_period.is_ready()){
        giro.update(giro_period.get_dt());
        car.giro_angles[0] = giro.giro_angles[0];
        car.giro_angles[1] = giro.giro_angles[1];
        car.giro_angles[2] = giro.giro_angles[2];

        car.acell[0] = giro.ax;
        car.acell[1] = giro.ay;
        car.acell[2] = giro.az;
    }
    
    car.update();

    //чтение данных из ком порта
    while (Serial.available())
    {
        buffer[buffer_size] = Serial.read();
        //буффер собран
        if ( buffer[0] == buffer_size)
        {
            car.process_command(&buffer[1], buffer[0]);
            buffer_size = 0;
        }
        else
        {
            buffer_size++;
        }
    }
}
