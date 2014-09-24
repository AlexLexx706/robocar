#ifndef PERIOD_H
#define PERIOD_H
//сласс для проверки интервалов
class Period{
    unsigned long st;
    unsigned long duration;
public:
    
    Period(unsigned long duration_mk):duration(duration_mk){st = micros();}

    bool isReady(){
        //проверка выключена
        if (duration == 0xffffffff)
            return false;

        unsigned long ct = micros();
        unsigned long dt = ct - st;
        
        if (dt < duration)
            return false;

        st = ct;
        return true;
    }

    void set_period(unsigned long duration_ms){
        duration = duration_ms;
    }
};
#endif
