#include "car.h"
#include <SPI.h>
#include "my_pid.h"
#include "I2Cdev.h"
#include "MPU6050_6Axis_MotionApps20.h"
#include "Wire.h"
#include <MsTimer2.h>
//#include <eRCaGuy_Timer2_Counter.h>

#define LEFT_SPEED_COUNTER_PIN 4
#define RIGHT_SPEED_COUNTER_PIN 10

uint8_t latest_interrupted_pin;

static MPU6050 mpu;
static bool dmpReady = false;  // set true if DMP init was successful
static uint8_t mpuIntStatus;   // holds actual interrupt status byte from MPU
static uint16_t packetSize;    // expected DMP packet size (default is 42 bytes)
static uint16_t fifoCount;     // count of all bytes currently in FIFO
static uint8_t fifoBuffer[64]; // FIFO storage buffer

// orientation/motion vars
static Quaternion q;           // [w, x, y, z]         quaternion container
static volatile bool mpuInterrupt = false;     // indicates whether MPU interrupt pin has gone high
static Car car;
static uint8_t buffer[33];
static uint8_t buffer_size = 0;


void dmpDataReady()
{
    mpuInterrupt = true;
}


void update_wheel_speed()
{
    car.wheel_left.updata_count();
    car.wheel_right.updata_count();
}

void update_dmp6(float euler[3])
{
    // if programming failed, don't try to do anything
    if (!dmpReady) return;

    // wait for MPU interrupt or extra packet(s) available
    while (!mpuInterrupt && fifoCount < packetSize){}

    // reset interrupt flag and get INT_STATUS byte
    mpuInterrupt = false;
    mpuIntStatus = mpu.getIntStatus();

    // get current FIFO count
    fifoCount = mpu.getFIFOCount();

    // check for overflow (this should never happen unless our code is too inefficient)
    if ((mpuIntStatus & 0x10) || fifoCount == 1024)
        mpu.resetFIFO();

    // otherwise, check for DMP data ready interrupt (this should happen frequently)
    else if (mpuIntStatus & 0x02)
    {
        // wait for correct available data length, should be a VERY short wait
        while (fifoCount < packetSize) fifoCount = mpu.getFIFOCount();
        
        // read a packet from FIFO
        mpu.getFIFOBytes(fifoBuffer, packetSize);
        
        // track FIFO count here in case there is > 1 packet available
        // (this lets us immediately read more without waiting for an interrupt)
        fifoCount -= packetSize;
        
        mpu.dmpGetQuaternion(&q, fifoBuffer);
        mpu.dmpGetEuler(euler, &q);
    }
}



void setup() 
{ 
    Serial.begin(115200);
    Serial.println("Connect serial speed=115200!!!"); 

    car.wheel_left.set_power(0);
    car.wheel_right.set_power(0);

    //подключим шину I2C
    Wire.begin();
    TWBR = 24; // 400kHz I2C clock (200kHz if CPU is 8MHz)
    mpu.initialize();
    mpu.testConnection();
    uint8_t devStatus = mpu.dmpInitialize();

    // supply your own gyro offsets here, scaled for min sensitivity
    mpu.setXGyroOffset(220);
    mpu.setYGyroOffset(76);
    mpu.setZGyroOffset(-85);
    mpu.setZAccelOffset(1788); // 1688 factory default for my test chip

    // make sure it worked (returns 0 if so)
    if (devStatus == 0)
    {
        Serial.println("mpu.setDMPEnabled");
        mpu.setDMPEnabled(true);
        attachInterrupt(0, dmpDataReady, RISING);
        mpuIntStatus = mpu.getIntStatus();
        dmpReady = true;
        packetSize = mpu.dmpGetFIFOPacketSize();
    }
    
    //запуск счёта скорости
    MsTimer2::set(0, update_wheel_speed);
    MsTimer2::start();
    //timer2.setup(); 
}

void loop() 
{
    update_dmp6(car.giro_angles);
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
