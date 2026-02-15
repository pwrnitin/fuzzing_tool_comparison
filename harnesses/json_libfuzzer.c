#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>

#include "json.h"
#include "json_object.h"
#include "json_tokener.h"

int LLVMFuzzerTestOneInput(const uint8_t *Data, size_t Size) {
    if (Size == 0) return 0;

    // Make a NUL-terminated copy for json-c
    char *buf = (char *)malloc(Size + 1);
    if (!buf) return 0;
    memcpy(buf, Data, Size);
    buf[Size] = '\0';

    struct json_tokener *tok = json_tokener_new();
    if (!tok) {
        free(buf);
        return 0;
    }

    struct json_object *obj = json_tokener_parse_ex(tok, buf, (int)Size);

    if (obj) {
        // Touch more code paths (helps coverage)
        (void)json_object_get_type(obj);
        (void)json_object_to_json_string_ext(obj, JSON_C_TO_STRING_PLAIN);
        json_object_put(obj);
    }

    json_tokener_free(tok);
    free(buf);
    return 0;
}

