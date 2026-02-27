// runtime/dictionary.c (Corrected and Final)

#include "dictionary.h"
#include <string.h>
#include <stdio.h>
#include "tusmo_runtime.h"
#include <gc.h>

#define QAAMUUS_INITIAL_CAPACITY 16

// A simple djb2 hash function for strings
static unsigned long hash_key(const char* key) {
    unsigned long hash = 5381;
    int c;
    while ((c = *key++)) {
        hash = ((hash << 5) + hash) + c; // hash * 33 + c
    }
    return hash;
}

TusmoQaamuus* tusmo_qaamuus_create() {
    TusmoQaamuus* qaamuus = (TusmoQaamuus*)GC_MALLOC(sizeof(TusmoQaamuus));
    qaamuus->capacity = QAAMUUS_INITIAL_CAPACITY;
    qaamuus->count = 0;
    qaamuus->entries = (TusmoQaamuusEntry**)GC_MALLOC(sizeof(TusmoQaamuusEntry*) * qaamuus->capacity);
    for (size_t i = 0; i < qaamuus->capacity; i++) {
        qaamuus->entries[i] = NULL;
    }
    return qaamuus;
}

static void tusmo_qaamuus_resize(TusmoQaamuus* qaamuus) {
    if (qaamuus->count < qaamuus->capacity * 0.75) return;

    size_t new_capacity = qaamuus->capacity * 2;
    TusmoQaamuusEntry** new_entries = (TusmoQaamuusEntry**)GC_MALLOC(sizeof(TusmoQaamuusEntry*) * new_capacity);
    for (size_t i = 0; i < new_capacity; i++) new_entries[i] = NULL;

    for (size_t i = 0; i < qaamuus->capacity; i++) {
        TusmoQaamuusEntry* entry = qaamuus->entries[i];
        while (entry) {
            TusmoQaamuusEntry* next = entry->next;
            unsigned long index = hash_key(entry->key) % new_capacity;
            entry->next = new_entries[index];
            new_entries[index] = entry;
            entry = next;
        }
    }

    qaamuus->entries = new_entries;
    qaamuus->capacity = new_capacity;
}

void tusmo_qaamuus_set(TusmoQaamuus* qaamuus, const char* key, TusmoValue value) {
    tusmo_qaamuus_resize(qaamuus);
    unsigned long index = hash_key(key) % qaamuus->capacity;
    TusmoQaamuusEntry* entry = qaamuus->entries[index];

    while (entry != NULL) {
        if (strcmp(entry->key, key) == 0) {
            entry->value = value;
            return;
        }
        entry = entry->next;
    }

    TusmoQaamuusEntry* new_entry = (TusmoQaamuusEntry*)GC_MALLOC(sizeof(TusmoQaamuusEntry));
    new_entry->key = (char*)GC_MALLOC(strlen(key) + 1);
    strcpy(new_entry->key, key);
    new_entry->value = value;
    new_entry->next = qaamuus->entries[index];
    qaamuus->entries[index] = new_entry;
    qaamuus->count++;
}

// Forward declaration for recursive printing
void tusmo_qor_dynamic_value(TusmoValue val);

void tusmo_qaamuus_print(TusmoQaamuus* qaamuus) {
    printf("{");
    int first = 1;
    for (size_t i = 0; i < qaamuus->capacity; i++) {
        TusmoQaamuusEntry* entry = qaamuus->entries[i];
        while (entry) {
            if (!first) {
                printf(", ");
            }
            printf("\"%s\": ", entry->key);
            tusmo_qor_dynamic_value(entry->value);
            first = 0;
            entry = entry->next;
        }
    }
    printf("}");
}

TusmoValue tusmo_qaamuus_get(TusmoQaamuus* qaamuus, const char* key) {
    unsigned long index = hash_key(key) % qaamuus->capacity;
    TusmoQaamuusEntry* entry = qaamuus->entries[index];

    while (entry != NULL) {
        if (strcmp(entry->key, key) == 0) {
            return entry->value;
        }
        entry = entry->next;
    }

    // Return TUSMO_WAXBA if not found
    TusmoValue not_found;
    not_found.type = TUSMO_WAXBA;
    return not_found;
}

void tusmo_qaamuus_delete(TusmoQaamuus* qaamuus, const char* key) {
    unsigned long index = hash_key(key) % qaamuus->capacity;
    TusmoQaamuusEntry* entry = qaamuus->entries[index];
    TusmoQaamuusEntry* prev = NULL;

    while (entry != NULL) {
        if (strcmp(entry->key, key) == 0) {
            if (prev == NULL) {
                qaamuus->entries[index] = entry->next;
            } else {
                prev->next = entry->next;
            }
            qaamuus->count--;
            return;
        }
        prev = entry;
        entry = entry->next;
    }
}

bool tusmo_qaamuus_has_key(TusmoQaamuus* qaamuus, const char* key) {
    unsigned long index = hash_key(key) % qaamuus->capacity;
    TusmoQaamuusEntry* entry = qaamuus->entries[index];

    while (entry != NULL) {
        if (strcmp(entry->key, key) == 0) {
            return true;
        }
        entry = entry->next;
    }
    return false;
}

