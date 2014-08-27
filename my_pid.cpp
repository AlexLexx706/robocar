#include "my_pid.h"
#include <Arduino.h>

PID::PID(double * _error, double * _output, double _kp, double _ki, double _kd):
kp(_kp),
ki(_ki),
kd(_kd),
error(_error),
output(_output),
prew_error(0),
ci(0),
prew_time(0),
out_min(-1),
out_max(1),
first(true)
{
}

void PID::Compute() {
    if (first) {
        prew_time = micros();
        prew_error = *error;
        first = false;
        ci = 0;
    }
    unsigned long cur_time = micros();
    double dt = (cur_time - prew_time) / 1000000.;
    double de = *error - prew_error;
    double cp = kp * (*error);
    double cd = 0;
    
    ci += (*error) * dt;

    if (dt > 0)
        cd = de / dt;

    prew_time = cur_time;
    prew_error = *error;
    (*output) = cp + (ki * ci) + (kd * cd);
    
    if ((*output) < out_min)
        (*output) = out_min;
    else if ((*output) > out_max)
        (*output) = out_max;
}

void PID::SetOutputLimits(double min, double max){
    out_min = min;
    out_max = max;
}

void PID::SetTunings( double p, double i, double d){
    kp = p;
    ki = i;
    kd = d;
    prew_time = millis();
    prew_error = (*error);
    first = false;
    ci = 0;
}
