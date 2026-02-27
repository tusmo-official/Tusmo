// runtime/string.c

#include "tusmo_runtime.h"

char* tusmo_str_format(const char* format, ...) {
    va_list args1, args2;
    va_start(args1, format);
    va_copy(args2, args1);
    int size = vsnprintf(NULL, 0, format, args1);
    va_end(args1);
    if (size < 0) return NULL;
    char* buffer = GC_MALLOC(size + 1);
    if (!buffer) return NULL;
    vsnprintf(buffer, size + 1, format, args2);
    va_end(args2);
    return buffer;
}

static const char* tusmo_safe_cstr(const char* value) {
    if (!value) {
        return "";
    }
    uintptr_t addr = (uintptr_t)value;
    if (addr < 4096) {
        return "";
    }
    return value;
}

char* tusmo_concat_cstr(const char* left, const char* right) {
    const char* safe_left = tusmo_safe_cstr(left);
    const char* safe_right = tusmo_safe_cstr(right);
    return tusmo_str_format("%s%s", safe_left, safe_right);
}
