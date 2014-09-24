/*
  Ultrasonic.cpp - Library for HC-SR04 Ultrasonic Ranging Module.library

  Created by ITead studio. Apr 20, 2010.
  iteadstudio.com
  
  updated by noonv. Feb, 2011
  http://robocraft.ru
*/

#include "Ultrasonic.h"

Ultrasonic::Ultrasonic(int TP, int EP, unsigned long max_period_mk)
{
   pinMode(TP, OUTPUT);
   pinMode(EP, INPUT);
   Trig_pin=TP;
   Echo_pin=EP;
   max_period = max_period_mk;
}

long Ultrasonic::Timing()
{
  digitalWrite(Trig_pin, LOW);
  delayMicroseconds(2);
  digitalWrite(Trig_pin, HIGH);
  delayMicroseconds(10);
  digitalWrite(Trig_pin, LOW);
  duration = pulseIn(Echo_pin, HIGH, max_period);

  if (duration == 0)
      duration = max_period;

  return duration;
}

long Ultrasonic::Ranging()
{
  Timing();
  distacne_cm = duration /29 / 2;
  return distacne_cm;
}
