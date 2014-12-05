#ifndef MY_PID_h
#define MY_PID_h
#include <Arduino.h>
#include <period.h>
class PID
{
public:
    PID(float * error, float * power, float p, float i, float d);
    void Compute(float dt = 0.0);
    void SetOutputLimits(float min, float max);
    void SetTunings(float p, float i, float d);
    void Reset();
private:
    float kp;
    float ki;
    float kd;
    float * error;
    float * output;
    float  prew_error;
    float ci;
    bool first;
    float out_min, out_max;
    Period period;
};
#endif

