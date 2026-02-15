#include <stdio.h>
#include <stdlib.h>
#include "json.h"
#include "json_object.h"

int main(int argc, char **argv) {
    if (argc < 2) return 0;

    FILE *f = fopen(argv[1], "rb");
    if (!f) return 0;

    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    if (sz <= 0 || sz > 1024 * 1024) { fclose(f); return 0; }
    fseek(f, 0, SEEK_SET);

    char *buf = (char *)malloc((size_t)sz + 1);
    if (!buf) { fclose(f); return 0; }

    fread(buf, 1, (size_t)sz, f);
    fclose(f);
    buf[sz] = '\0';

    struct json_tokener *tok = json_tokener_new();
    if (!tok) { free(buf); return 0; }

    json_object *obj = json_tokener_parse_ex(tok, buf, (int)sz);

    if (obj) json_object_put(obj);
    json_tokener_free(tok);
    free(buf);
    return 0;
}

