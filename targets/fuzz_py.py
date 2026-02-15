import atheris
import sys

def target_function(data: bytes):
    # simple example: decode + parse-like behavior
    s = data.decode("utf-8", errors="ignore")

    # pretend-bug: crash if trigger appears
    if "CRASH" in s or s.count("{")>50:
        raise RuntimeError("Triggered crash")

    # do some work so fuzzer has branches
    if s.startswith("{") and s.endswith("}"):
        if "admin" in s:
            pass

def TestOneInput(data):
    target_function(data)

def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()

if __name__ == "__main__":
    main()
