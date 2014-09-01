#ifndef MY_PID_h
#define MY_PID_h

class PID
{
public:
    PID(double * error, double * power, double p, double i, double d);
    void Compute();
    void SetOutputLimits(double min, double max);
    void SetTunings(double p, double i, double d);
private:
    double kp;
    double ki;
    double kd;
    double * error;
    double * output;
    double  prew_error;
    double ci;
    bool first;

    unsigned long prew_time;
    double out_min, out_max;
};
#endif

