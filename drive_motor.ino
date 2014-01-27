
float time = 0;
#define m1_f 3
#define m1_b 5

#define m2_f 6
#define m2_b 9
#define SPEED 100


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
} 
 
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
        
//    float v = cos(time) * 255;
//    
//    if ( v >  0.0 )
//    {
//        analogWrite(m1_f, v);
//        digitalWrite(m1_b, LOW);
//
//        analogWrite(m2_f, v);
//        digitalWrite(m2_b, LOW);
//    }
//    else
//    {
//        analogWrite(m1_b, -v);
//        digitalWrite(m1_f, LOW);
//
//        analogWrite(m2_b, -v);
//        digitalWrite(m2_f, LOW);
//    }
//    time = time + 0.05;
//    delay(100);
} 
