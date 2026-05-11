/*
 * File-based harness for Fuzzgoat (used by AFL++ and Honggfuzz).
 * Reads the input file passed on argv[1] and calls json_parse().
 */

#include <stdio.h>
#include <stdlib.h>
#include "fuzzgoat.h"

extern json_value *json_parse(const json_char *json, size_t length);
extern void json_value_free(json_value *value);

int main(int argc, char **argv) {
    if (argc < 2) return 0;

    FILE *f = fopen(argv[1], "rb");
    if (!f) return 0;

    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    if (sz <= 0 || sz > 1024 * 1024) { fclose(f); return 0; }
    fseek(f, 0, SEEK_SET);

    char *buf = (char *)malloc((size_t)sz);
    if (!buf) { fclose(f); return 0; }

    if (fread(buf, 1, (size_t)sz, f) != (size_t)sz) {
        fclose(f);
        free(buf);
        return 0;
    }
    fclose(f);

    json_value *value = json_parse((const json_char *)buf, (size_t)sz);
    if (value != NULL) {
        json_value_free(value);
    }

    free(buf);
    return 0;
}
