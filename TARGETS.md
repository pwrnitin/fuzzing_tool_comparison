# External Targets and Tools

The fuzzing targets and tools used in this study are cloned from their upstream
repositories at build time and are not committed to this repository (see
`.gitignore`). To reproduce the experiments, recreate the directory layout
documented below.

## Fuzzing Targets

### json-c
- Upstream: https://github.com/json-c/json-c
- Version: 0.17
- Clone location: `targets/json-c/`

### libpng
- Upstream: https://github.com/glennrp/libpng
- Version: 1.6.40
- Clone location: `targets/libpng/`

### Fuzzgoat
- Upstream: https://github.com/fuzzstati0n/fuzzgoat
- Commit: `4a75a74f239514ffdaec499f00f642fdaf897931`
- Clone location: `targets/fuzzgoat/`
- Purpose: Small C JSON parser with **four deliberately planted memory-corruption
  bugs**, documented in `fuzzgoat.c` with `WARNING: Fuzzgoat Vulnerability`
  comments. Used as the known-bug target with ground-truth trigger inputs
  (`input-files/emptyArray`, `emptyString`, `oneByteString`, `validObject`).

To reproduce exactly:
```bash
git clone https://github.com/fuzzstati0n/fuzzgoat.git targets/fuzzgoat
cd targets/fuzzgoat && git checkout 4a75a74f239514ffdaec499f00f642fdaf897931
```

## Fuzzing Tools

| Tool       | Source                                      | Version       |
|------------|---------------------------------------------|---------------|
| AFL++      | Ubuntu apt package `afl++`                  | 4.09c         |
| LibFuzzer  | Bundled with Clang/LLVM compiler-rt         | LLVM 18       |
| Honggfuzz  | https://github.com/google/honggfuzz (built from source) | 2.6 |

## Sanitizer Configuration

All Fuzzgoat builds use AddressSanitizer + UndefinedBehaviorSanitizer
(`-fsanitize=address,undefined`) to detect memory-corruption bugs and undefined
behaviour at runtime.
