// runtime/random.c
#include "tusmo_runtime.h"
#include <time.h>

void tusmo_init_random() {
    srand((unsigned int)time(NULL));
}

int tusmo_random_int(int min, int max) {
    if (min > max) {
        // Handle error: swap, return error code, or assert
        int temp = min;
        min = max;
        max = temp;
    }
    
    // Prevent overflow by using unsigned arithmetic
    unsigned int range = (unsigned int)max - (unsigned int)min + 1;
    return min + rand() % range;
}

double tusmo_random_double(double min, double max) {
    if (min > max) {
        // Handle error: swap, return error code, or assert
        double temp = min;
        min = max;
        max = temp;
    }

    double scale = rand() / (double)RAND_MAX;
    return min + scale * (max - min);
}
