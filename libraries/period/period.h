#ifndef PERIOD_H
#define PERIOD_H
//сласс для проверки интервалов
class Period{
    unsigned long st;
    unsigned long duration;
    unsigned long dt;
public:
    
    Period(unsigned long duration_mk):st(micros()), duration(duration_mk) {}

    bool is_ready(){
        //проверка выключена
        if (duration == 0xffffffff)
            return false;

        unsigned long ct = micros();
        dt = ct - st;
        
        if (dt < duration)
            return false;

        st = ct - (dt % duration);
        return true;
    }
    
    void reset() {st = micros();}

    void set_period(unsigned long duration_ms){
        duration = duration_ms;
    }
    unsigned long get_period() const {return duration;}

    float get_dt() const{return dt / 1000000.0;}
};
#endif
