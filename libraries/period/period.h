#ifndef PERIOD_H
#define PERIOD_H
//сласс для проверки интервалов
class Period{
    unsigned long st;
    unsigned long duration;
    float last_dt;
public:
    
    Period(unsigned long duration_mk):duration(duration_mk), last_dt(0.1) {st = micros();}

    bool is_ready(){
        //проверка выключена
        if (duration == 0xffffffff)
            return false;

        unsigned long ct = micros();
        unsigned long dt = ct - st;
        
        if (dt < duration)
            return false;

        last_dt = dt / 1000000.;
        st = ct - (dt % duration);
        return true;
    }
    
    void reset() {st = micros();}

    void set_period(unsigned long duration_ms){
        duration = duration_ms;
    }

    float get_dt() const {return last_dt;}
};
#endif
