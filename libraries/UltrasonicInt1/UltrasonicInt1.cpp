#include "UltrasonicInt1.h"
#define ECHO_PIN 3
#define RELEASE_TIMEOUT 10000

UltrasonicInt1 us_int1;

void echo_falling(){
    us_int1.duration = micros() - us_int1.start_time;
    us_int1.complete = true;
}


void UltrasonicInt1::init(int _trig_pin, unsigned long max_distance) {
    trig_pin = _trig_pin;
    max_duraion = (max_distance + 7) * 58;
    distance = max_distance;

    pinMode(trig_pin, OUTPUT);
    digitalWrite(trig_pin, LOW);
    pinMode(ECHO_PIN, INPUT);
    digitalWrite(ECHO_PIN, LOW);
    attachInterrupt(1, echo_falling, FALLING);
   
    ready = true;
    complete = false;
    wait_ready = false;
}

boolean UltrasonicInt1::update(){
    //prepare for start
    if (wait_ready){
        if ((micros() - start_time) >= RELEASE_TIMEOUT )
        {
            ready = true;
            wait_ready = false;
        }
        return false;
    }
    
    //start measure
    if (ready){
        ready = false;
        complete = false;
        
        delayMicroseconds(1);
        digitalWrite(trig_pin, HIGH);
        delayMicroseconds(5);
        digitalWrite(trig_pin, LOW);
        start_time = micros();
        return false;
    }
    unsigned long ct = micros();
    
    //check for complete
    if (complete || (ct - start_time) >= max_duraion){
        if (!complete){
            duration = max_duraion;
            ready = true;
        }
        else{
            wait_ready = true;
        }

        start_time = ct;
        distance = (duration / 58) - 7;
        return true;
    }
    return false;
}

