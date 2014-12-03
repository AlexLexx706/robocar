#ifndef MPU6050_SIMPLE_GIRO
#define MPU6050_SIMPLE_GIRO

#include "I2Cdev.h"
#include "MPU6050.h"

#define CALIBRATION_READ 100
#define PI 3.14159

//Compute giro angles for raw data MPU6050
class Giro {
public:
    //angles of giro
    float giro_angles[3];
    
    //raw data of MPU6050
    int16_t ax, ay, az, gx, gy, gz;

    //constructor
    Giro():ax(0), ay(0), az(0), gx(0), gy(0), gz(0){
        giro_angles[0] = 0.0;
        giro_angles[1] = 0.0;
        giro_angles[2] = 0.0;
    }
    
    //make mpu6050 initialization and create calibration
    void init(){
        Wire.begin();
        accelgyro.initialize();
        calibrate_gyro();
    }
    
    //angle calculation
    void update(float dt) {
        accelgyro.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);
        giro_angles[0] += (gx - giro_zerro[0]) / 131. / 180.0 * PI * dt;
        giro_angles[1] += (gy - giro_zerro[1]) / 131. / 180.0 * PI * dt;
        giro_angles[2] += (gz - giro_zerro[2]) / 131. / 180.0 * PI * dt;
    }

private:
    MPU6050 accelgyro;
    int16_t giro_zerro[3];
    
    //calibrate giro offset
    void calibrate_gyro() {
        long value[3] = {0, 0, 0};

        for (int i = 0; i < CALIBRATION_READ; i++) {
            accelgyro.getRotation(&giro_zerro[0], &giro_zerro[1], &giro_zerro[2]);
            value[0] += giro_zerro[0];
            value[1] += giro_zerro[1];
            value[2] += giro_zerro[2];
        }
        giro_zerro[0] = value[0] / CALIBRATION_READ;
        giro_zerro[1] = value[1] / CALIBRATION_READ;
        giro_zerro[2] = value[2] / CALIBRATION_READ;
    }
};
#endif
