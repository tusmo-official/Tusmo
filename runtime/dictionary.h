// runtime/dictionary.h (Corrected and Final)

#ifndef DICTIONARY_H
#define DICTIONARY_H

#include <stddef.h>
#include "tusmo_types.h"
#include <stdbool.h>

// Structure for a single key-value entry in the dictionary
typedef struct TusmoQaamuusEntry {
    char* key;
    TusmoValue value;
    struct TusmoQaamuusEntry* next;
} TusmoQaamuusEntry;

// The main dictionary structure (hash table)
typedef struct TusmoQaamuus {
    TusmoQaamuusEntry** entries;
    size_t capacity;
    size_t count;
} TusmoQaamuus;

// --- FUNCTION PROTOTYPES ---

TusmoQaamuus* tusmo_qaamuus_create();
void tusmo_qaamuus_set(TusmoQaamuus* qaamuus, const char* key, TusmoValue value);
void tusmo_qaamuus_print(TusmoQaamuus* qaamuus);
TusmoValue tusmo_qaamuus_get(TusmoQaamuus* qaamuus, const char* key);
void tusmo_qaamuus_delete(TusmoQaamuus* qaamuus, const char* key);
bool tusmo_qaamuus_has_key(TusmoQaamuus* qaamuus, const char* key);

#endif // DICTIONARY_H
