#include "car.h"
#include <SPI.h>
#include <RF24.h>


#include "I2Cdev.h"
#include "MPU6050_6Axis_MotionApps20.h"
#include "Wire.h"


MPU6050 mpu;
bool dmpReady = false;  // set true if DMP init was successful
uint8_t mpuIntStatus;   // holds actual interrupt status byte from MPU
uint8_t devStatus;      // return status after each device operation (0 = success, !0 = error)
uint16_t packetSize;    // expected DMP packet size (default is 42 bytes)
uint16_t fifoCount;     // count of all bytes currently in FIFO
uint8_t fifoBuffer[64]; // FIFO storage buffer

// orientation/motion vars
Quaternion q;           // [w, x, y, z]         quaternion container
volatile bool mpuInterrupt = false;     // indicates whether MPU interrupt pin has gone high

void dmpDataReady()
{
    mpuInterrupt = true;
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


Car car;
RF24 radio(A0, 10);
const uint64_t pipes[2] = {0X0202020202LL, 0X0101010101LL};


void setup() 
{ 
    Serial.begin(115200);
    Serial.println("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!");
    
    car.wheel_left.set_power(0);
    car.wheel_right.set_power(0);

    radio.begin();
    radio.setChannel(66);
    radio.setDataRate(RF24_2MBPS);
    radio.setAutoAck(true);
    radio.setCRCLength(RF24_CRC_8);
    radio.setRetries(15,15);
    radio.setPayloadSize(32);
    radio.openReadingPipe(0, pipes[0]);
    radio.openReadingPipe(1, pipes[1]);
    radio.startListening();
    radio.enableDynamicPayloads();
    
    // join I2C bus (I2Cdev library doesn't do this automatically)
    Wire.begin();
    TWBR = 24; // 400kHz I2C clock (200kHz if CPU is 8MHz)
    Serial.println("mpu.initialize");
    mpu.initialize();
    Serial.println("mpu.testConnection");
    mpu.testConnection();
    Serial.println("mpu.dmpInitialize");
    devStatus = mpu.dmpInitialize();

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
}

void loop() 
{
    update_dmp6(car.giro_angles);
    car.update();
    //проверка данных
    if (radio.available())
    {
        uint8_t size = radio.getDynamicPayloadSize();
        uint8_t data[33];
        radio.read(data, size);
        car.process_command(&data[1], size);
    }
}
