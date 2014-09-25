#include <UltrasonicInt1.h>

void setup()
{
    Serial.begin(115200);
    us_int1.init(7);
}

void loop()
{
    if ( us_int1.update() ){
        Serial.println(us_int1.get_distance());
    }
}