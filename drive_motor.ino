#include "Ultrasonic.h"
#include "Wire.h"
#include "I2Cdev.h"
#include "HMC5883L.h"

#define m1_f 3
#define m1_b 10

#define m2_f 6
#define m2_b 9
#define SPEED 80

#define min_len 8
#define max_len 30
bool need_move = false;


// class default I2C address is 0x1E
// specific I2C addresses may be passed as a parameter here
// this device only supports one I2C address (0x1E)
HMC5883L mag;
int16_t mx, my, mz;

// sensor connected to:
// Trig - 12, Echo - 13
Ultrasonic ultrasonic(12, 13);

void setup() 
{ 
    pinMode(m1_f, OUTPUT);   // sets the pin as output
    pinMode(m1_b, OUTPUT);   // sets the pin as output
    pinMode(m2_f, OUTPUT);   // sets the pin as output
    pinMode(m2_b, OUTPUT);   // sets the pin as output


    digitalWrite(m1_f, LOW);   // sets the LED on
    digitalWrite(m1_b, LOW);   // sets the LED on

    digitalWrite(m2_f, LOW);   // sets the LED on
    digitalWrite(m2_b, LOW);   // sets the LED on

    Serial.begin(115200);

    //инициализация магнитометра
    Wire.begin();
    mag.initialize();
}


unsigned long start_time = millis();
void loop() 
{
    if ( Serial.available() )
    {
        uint8_t data = Serial.read();
        uint8_t l = data >> 2;
        uint8_t r = data & 3;
        
        if (l == 0)
        {
            digitalWrite(m1_f, LOW);
            digitalWrite(m1_b, LOW);
        }
        else if (l == 1)
        {
            //digitalWrite(m1_f, HIGH);
            analogWrite(m1_f, SPEED);
            digitalWrite(m1_b, LOW);
        }
        else
        {
            digitalWrite(m1_f, LOW);
            //digitalWrite(m1_b, HIGH);
            analogWrite(m1_b, SPEED);
        }
        
        
        if (r == 0)
        {
            digitalWrite(m2_f, LOW);
            digitalWrite(m2_b, LOW);
        }
        else if (r == 1)
        {
            //digitalWrite(m2_f, HIGH);
            analogWrite(m2_f, SPEED);
            digitalWrite(m2_b, LOW);
        }
        else
        {
            digitalWrite(m2_f, LOW);
            //digitalWrite(m2_b, HIGH);
            analogWrite(m2_b, SPEED);
        }
    }
    else
    {
        if ( millis() > start_time + 100 )
        {       
            float dist_cm = ultrasonic.Ranging(CM);
            start_time = millis();
            
            //уход от препятствия.
            if ( dist_cm < min_len )
            {
                need_move = true;
            }
            else if ( need_move && dist_cm > max_len ) 
            {
                need_move = false;
            }
            
            //
            if (need_move)
            {
                analogWrite(m1_b, SPEED);
                digitalWrite(m1_f, LOW);
    
                analogWrite(m2_b, SPEED);
                digitalWrite(m2_f, LOW);
            }
            else
            {
                digitalWrite(m1_b, LOW);
                digitalWrite(m2_b, LOW);
            }
        }
    }
    
    //получаем направление.
    mag.getHeading(&mx, &my, &mz);
    float heading = atan2(my, mx);

    if(heading < 0)
        heading += 2 * M_PI;
    
} 
