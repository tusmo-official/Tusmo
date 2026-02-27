#include "tusmo_runtime.h"

// Generic finalizer and grow helpers can be shared if they are not static,
// or you can copy them here. For simplicity, we'll assume they are available
// or redefined here.
// Dhamaystirka guud iyo caawiyayaasha koray waa la wadaagi karaa haddi aanay fadhiyin,
// ama waad koobi kartaa iyaga halkan. Si ay u fududaato, waxaanu u qaadan doonaa inay diyaar yihiin
// ama halkan lagu qeexay.
static void tusmo_tix_data_finalizer(void* obj, void* client_data) {
    void** data_ptr = (void**)obj;
    if (*data_ptr) {
        free(*data_ptr);
        *data_ptr = NULL;
    }
}

static inline void tusmo_hp_grow_if_needed(void** data, size_t* capacity, size_t new_size, size_t elem_size) {
    if (__builtin_expect(new_size > *capacity, 0)) {
        size_t new_capacity = (*capacity == 0) ? 8 : *capacity * 2;
        if (new_capacity < new_size) new_capacity = new_size;
        *data = realloc(*data, new_capacity * elem_size);
        if (!*data) { perror("realloc failed"); exit(1); }
        *capacity = new_capacity;
    }
}


// --- Implementation for the Generic Array ---

TusmoTixGeneric* tusmo_tix_generic_create(size_t cap) {
    TusmoTixGeneric* tix = GC_MALLOC(sizeof(TusmoTixGeneric));
    // The data it holds are pointers to other GC-managed objects.
    tix->data = malloc(cap * sizeof(void*));
    tix->size = 0;
    tix->capacity = cap;
    GC_REGISTER_FINALIZER(tix, tusmo_tix_data_finalizer, NULL, NULL, NULL);
    return tix;
}

void tusmo_tix_generic_append(TusmoTixGeneric* tix, void* value) {
    tusmo_hp_grow_if_needed((void**)&tix->data, &tix->capacity, tix->size + 1, sizeof(void*));
    tix->data[tix->size++] = value;
}

void tusmo_tix_generic_insert(TusmoTixGeneric* tix, size_t index, void* value) {
    if (index > tix->size) {
        fprintf(stderr, "Cilad: Tusmo, index-ka %zu wuu ka weyn yahay cabbirka %zu\n", index, tix->size);
        exit(1);
    }
    tusmo_hp_grow_if_needed((void**)&tix->data, &tix->capacity, tix->size + 1, sizeof(void*));
    if (index < tix->size) {
        memmove(&tix->data[index + 1], &tix->data[index], (tix->size - index) * sizeof(void*));
    }
    tix->data[index] = value;
    tix->size++;
}

void* tusmo_tix_generic_pop(TusmoTixGeneric* tix, size_t index) {
    if (index >= tix->size) {
        fprintf(stderr, "Cilad: Tusmo, index-ka %zu wuu ka baxsan yahay xadka %zu\n", index, tix->size);
        exit(1);
    }
    void* val = tix->data[index];
    if (index < tix->size - 1) {
        memmove(&tix->data[index], &tix->data[index + 1], (tix->size - 1 - index) * sizeof(void*));
    }
    tix->size--;
    // Optional: shrink if capacity is much larger than size
    return val;
}

bool tusmo_tix_generic_remove(TusmoTixGeneric* tix, void* value) {
    for (size_t i = 0; i < tix->size; i++) {
        // Checking for pointer equality for nested arrays
        if (tix->data[i] == value) {
            tusmo_tix_generic_pop(tix, i);
            return true;
        }
    }
    return false;
}