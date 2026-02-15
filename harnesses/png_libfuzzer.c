#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <png.h>

int LLVMFuzzerTestOneInput(const uint8_t *Data, size_t Size) {
    if (Size == 0 || Size > 2 * 1024 * 1024) return 0;

    png_image img;
    memset(&img, 0, sizeof(img));
    img.version = PNG_IMAGE_VERSION;

    if (png_image_begin_read_from_memory(&img, Data, Size)) {
        img.format = PNG_FORMAT_RGBA;
        size_t out_sz = PNG_IMAGE_SIZE(img);
        void *out = malloc(out_sz);
        if (out) {
            png_image_finish_read(&img, NULL, out, 0, NULL);
            free(out);
        }
        png_image_free(&img);
    }
    return 0;
}

