/*
 * LibFuzzer harness for Fuzzgoat.
 * Calls json_parse() directly on the in-process input buffer.
 */

#include <stdint.h>
#include <stddef.h>
#include "fuzzgoat.h"

extern json_value *json_parse(const json_char *json, size_t length);
extern void json_value_free(json_value *value);

int LLVMFuzzerTestOneInput(const uint8_t *Data, size_t Size) {
    if (Size == 0) return 0;
    json_value *value = json_parse((const json_char *)Data, Size);
    if (value != NULL) {
        json_value_free(value);
    }
    return 0;
}
