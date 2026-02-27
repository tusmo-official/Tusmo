// runtime/type_conversion.c

#include "type_conversion.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <gc.h>

// Convert any TusmoValue to a string (eray)
char* tusmo_to_eray(TusmoValue val) {
    char* buffer = GC_MALLOC(128); // Allocate a buffer
    switch (val.type) {
        case TUSMO_TIRO:
            snprintf(buffer, 128, "%d", val.value.as_tiro);
            break;
        case TUSMO_JAJAB:
            snprintf(buffer, 128, "%f", val.value.as_jajab);
            break;
        case TUSMO_ERAY:
            return val.value.as_eray; // Already a string
        case TUSMO_MIYAA:
            return val.value.as_miyaa ? "run" : "been";
        case TUSMO_XARAF:
            snprintf(buffer, 128, "%c", val.value.as_xaraf);
            break;
        case TUSMO_QAAMUUS:
            return "<qaamuus>";
        case TUSMO_TIX:
            return "<tix>";
        default:
            return "<nooc aan la menneyn>";
    }
    return buffer;
}

// Convert any TusmoValue to an integer (tiro)
int tusmo_to_tiro(TusmoValue val) {
    switch (val.type) {
        case TUSMO_TIRO:
            return val.value.as_tiro;
        case TUSMO_JAJAB:
            return (int)val.value.as_jajab;
        case TUSMO_ERAY:
            return atoi(val.value.as_eray);
        case TUSMO_MIYAA:
            return val.value.as_miyaa ? 1 : 0;
        case TUSMO_XARAF:
            return (int)val.value.as_xaraf;
        default:
            return 0;
    }
}

// Convert any TusmoValue to a double (jajab)
double tusmo_to_jajab(TusmoValue val) {
    switch (val.type) {
        case TUSMO_TIRO:
            return (double)val.value.as_tiro;
        case TUSMO_JAJAB:
            return val.value.as_jajab;
        case TUSMO_ERAY:
            return atof(val.value.as_eray);
        case TUSMO_MIYAA:
            return val.value.as_miyaa ? 1.0 : 0.0;
        case TUSMO_XARAF:
            return (double)val.value.as_xaraf;
        default:
            return 0.0;
    }
}

// Convert any TusmoValue to a boolean (miyaa)
bool tusmo_to_miyaa(TusmoValue val) {
    switch (val.type) {
        case TUSMO_TIRO:
            return val.value.as_tiro != 0;
        case TUSMO_JAJAB:
            return val.value.as_jajab != 0.0;
        case TUSMO_ERAY:
            // Check for non-empty string
            return val.value.as_eray != NULL && val.value.as_eray[0] != '\0';
        case TUSMO_MIYAA:
            return val.value.as_miyaa;
        case TUSMO_XARAF:
            return val.value.as_xaraf != '\0';
        default:
            return false;
    }
}

char* tusmo_type_of(TusmoValue val) {
    switch (val.type) {
        case TUSMO_TIRO:   return "tiro";
        case TUSMO_JAJAB:  return "jajab";
        case TUSMO_ERAY:   return "eray";
        case TUSMO_MIYAA:  return "miyaa";
        case TUSMO_XARAF:  return "xaraf";
        case TUSMO_QAAMUUS:return "qaamuus";
        case TUSMO_TIX:    return "tix";
        default:           return "unknown";
    }
}
