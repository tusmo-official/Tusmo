// runtime/tusmo_types.h

#ifndef TUSMO_TYPES_H
#define TUSMO_TYPES_H

#include <stdbool.h>
#include <stddef.h>

struct TusmoQaamuus;
typedef struct TusmoTixMixed TusmoTixMixed;

typedef enum { TUSMO_TIRO, TUSMO_ERAY, TUSMO_JAJAB, TUSMO_MIYAA, TUSMO_XARAF, TUSMO_QAAMUUS, TUSMO_TIX, TUSMO_WAXBA } TusmoType;
typedef struct { TusmoType type; union { int as_tiro; char* as_eray; double as_jajab; bool as_miyaa; char as_xaraf; struct TusmoQaamuus* as_qaamuus; TusmoTixMixed* as_tix; } value; } TusmoValue;

#endif // TUSMO_TYPES_H
