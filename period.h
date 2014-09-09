#ifndef PERIOD_H
#define PERIOD_H
//сласс для проверки интервалов
class Period{
    unsigned long st;
    unsigned long duration;
public:
    
    Period(unsigned long duration_mk):duration(duration_mk){st = micros();}
    bool isReady(){
        unsigned long ct = micros();
        unsigned long dt = ct - st;
        
        if (dt < duration)
            return false;

        st = ct;
        return true;
    }
};
#endif
