#include "my_pid.h"
#include <Arduino.h>

PID::PID(float * _error, float * _output, float _kp, float _ki, float _kd):
kp(_kp),
ki(_ki),
kd(_kd),
error(_error),
output(_output),
prew_error(0),
ci(0),
out_min(-1),
out_max(1),
first(true),
dt(0.01)
{
}

void PID::Compute() {
    if (first) {
        prew_error = *error;
        first = false;
        ci = 0;
    }
    float de = *error - prew_error;
    float cp = kp * (*error);
    float cd = 0;
    
    ci += (*error) * dt;
    cd = de / dt;
    prew_error = *error;

    (*output) = cp + (ki * ci) + (kd * cd);

    if ((*output) < out_min)
        (*output) = out_min;
    else if ((*output) > out_max)
        (*output) = out_max;
}

void PID::SetOutputLimits(float min, float max){
    out_min = min;
    out_max = max;
}

void PID::SetTunings( float p, float i, float d){
    kp = p;
    ki = i;
    kd = d;
    first = true;
}

void PID::Reset(){
    first = true;
}

