#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <png.h>

int main(int argc, char **argv) {
    if (argc < 2) return 0;

    FILE *f = fopen(argv[1], "rb");
    if (!f) return 0;

    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    if (sz <= 0 || sz > 2 * 1024 * 1024) { fclose(f); return 0; }
    fseek(f, 0, SEEK_SET);

    unsigned char *buf = (unsigned char *)malloc((size_t)sz);
    if (!buf) { fclose(f); return 0; }

    fread(buf, 1, (size_t)sz, f);
    fclose(f);

    png_image img;
    memset(&img, 0, sizeof(img));
    img.version = PNG_IMAGE_VERSION;

    if (png_image_begin_read_from_memory(&img, buf, (size_t)sz)) {
        img.format = PNG_FORMAT_RGBA;
        size_t out_sz = PNG_IMAGE_SIZE(img);
        void *out = malloc(out_sz);
        if (out) {
            png_image_finish_read(&img, NULL, out, 0, NULL);
            free(out);
        }
        png_image_free(&img);
    }

    free(buf);
    return 0;
}

