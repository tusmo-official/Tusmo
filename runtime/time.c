#include "tusmo_runtime.h"
#include <time.h>
#include <unistd.h>

double tusmo_time() {
    return (double)time(NULL);
}

int tusmo_wait(int number) {
    // Shaxda 'sleep()' waxay u baahan tahay integer, waxayna sugtaa 'number' ilbiriqsiyo.
    // Waxay soo celinaysaa 0 haddii ay si guul leh u dhammaato ama wakhtiga haray haddii ay kala go'do.
    // Tusmo ahaan, waxaan soo celin karnaa 0 ama wax ka weyn.
    unsigned int remaining = sleep((unsigned int)number); 
    
    // Si la mid ah luuqadaha kale, waxaan soo celinaynaa 0 haddii ay si guul leh u shaqeyso.
    if (remaining == 0) {
        return 0; // Guul
    } else {
        return (int)remaining; // Haddii uu qalad jiro (tusaale, kala go' lagu sameeyay signal)
    }
}

char* tusmo_format_time(const char* format) {
    time_t rawtime;
    struct tm * timeinfo;
    char * buffer = (char *)GC_MALLOC(80 * sizeof(char));

    time(&rawtime);
    timeinfo = localtime(&rawtime);

    strftime(buffer, 80, format, timeinfo);
    return buffer;
}

int tusmo_get_seconds() {
    time_t rawtime;
    struct tm * timeinfo;
    time(&rawtime);
    timeinfo = localtime(&rawtime);
    return timeinfo->tm_sec;
}

int tusmo_get_minutes() {
    time_t rawtime;
    struct tm * timeinfo;
    time(&rawtime);
    timeinfo = localtime(&rawtime);
    return timeinfo->tm_min;
}

int tusmo_get_hours() {
    time_t rawtime;
    struct tm * timeinfo;
    time(&rawtime);
    timeinfo = localtime(&rawtime);
    return timeinfo->tm_hour;
}

int tusmo_get_day() {
    time_t rawtime;
    struct tm * timeinfo;
    time(&rawtime);
    timeinfo = localtime(&rawtime);
    return timeinfo->tm_mday;
}

int tusmo_get_month() {
    time_t rawtime;
    struct tm * timeinfo;
    time(&rawtime);
    timeinfo = localtime(&rawtime);
    return timeinfo->tm_mon + 1;
}

int tusmo_get_year() {
    time_t rawtime;
    struct tm * timeinfo;
    time(&rawtime);
    timeinfo = localtime(&rawtime);
    return timeinfo->tm_year + 1900;
}
