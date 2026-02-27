// runtime/io.c

#include "tusmo_runtime.h"


// --- Generic Printing Implementations ---
void prints_tix_tiro(TusmoTixTiro* tix) {
    printf("[");
    for (size_t i = 0; i < tix->size; i++) {
        printf("%d", tix->data[i]);
        if (i + 1 < tix->size) printf(", ");
    }
    printf("]");
}

void prints_tix_eray(TusmoTixEray* tix) {
    printf("[");
    for (size_t i = 0; i < tix->size; i++) {
        printf("\"%s\"", tix->data[i]);
        if (i + 1 < tix->size) printf(", ");
    }
    printf("]");
}

void prints_tix_jajab(TusmoTixJajab* tix) {
    printf("[");
    for (size_t i = 0; i < tix->size; i++) {
        printf("%f", tix->data[i]);
        if (i + 1 < tix->size) printf(", ");
    }
    printf("]");
}

void prints_tix_miyaa(TusmoTixMiyaa* tix) {
    printf("[");
    for (size_t i = 0; i < tix->size; i++) {
        printf(tix->data[i] ? "true" : "false");
        if (i + 1 < tix->size) printf(", ");
    }
    printf("]");
}

void prints_tix_mixed(TusmoTixMixed* tix) {
    printf("[");
    for (size_t i = 0; i < tix->size; i++) {
        tusmo_qor_dynamic_value(tix->data[i]);
        if (i + 1 < tix->size) printf(", ");
    }
    printf("]");
}

void tusmo_qor_dynamic_value(TusmoValue val) {
    switch (val.type) {
        case TUSMO_TIRO:  printf("%d", val.value.as_tiro); break;
        case TUSMO_ERAY:  printf("%s", val.value.as_eray); break;
        case TUSMO_JAJAB: printf("%f", val.value.as_jajab); break;
        case TUSMO_MIYAA: printf(val.value.as_miyaa ? "run" : "been"); break;
        case TUSMO_XARAF: printf("%c", val.value.as_xaraf); break;
        case TUSMO_QAAMUUS: tusmo_qaamuus_print(val.value.as_qaamuus); break;
        case TUSMO_TIX:  prints_tix_mixed(val.value.as_tix); break;
        case TUSMO_WAXBA: printf("waxba"); break;
        default:          printf("<nooc aan la aqoon>"); break;
    }
}

char* hel_str(void) {
    size_t size = 100;
    size_t len = 0;
    char* buffer = malloc(size);

    if (buffer == NULL) return NULL;

    int c;
    while ((c = getchar()) != '\n' && c != EOF) {
        buffer[len++] = c;

        if (len == size) {
            size *= 2;
            char* new_buffer = realloc(buffer, size);
            if (!new_buffer) {
                free(buffer);
                return NULL;
            }
            buffer = new_buffer;
        }
    }

    buffer[len] = '\0';
    return buffer;
}
