// runtime/type_conversion.h

#ifndef TYPE_CONVERSION_H
#define TYPE_CONVERSION_H

#include "tusmo_types.h"

// Conversion function prototypes
char* tusmo_to_eray(TusmoValue val);
int tusmo_to_tiro(TusmoValue val);
double tusmo_to_jajab(TusmoValue val);
bool tusmo_to_miyaa(TusmoValue val);
char* tusmo_type_of(TusmoValue val);

#endif // TYPE_CONVERSION_H
