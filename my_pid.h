#ifndef MY_PID_h
#define MY_PID_h

class PID
{
public:
    PID(float * error, float * power, float p, float i, float d);
    void Compute();
    void SetOutputLimits(float min, float max);
    void SetTunings(float p, float i, float d);
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
    float dt;
};
#endif

