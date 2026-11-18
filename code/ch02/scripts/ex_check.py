import json, struct, sys
sys.path.insert(0, sys.argv[2])
from stlib import read

SIZES = {"F64": 8, "F32": 4, "F16": 2, "BF16": 2, "I64": 8, "I32": 4,
         "I16": 2, "I8": 1, "U64": 8, "U32": 4, "U16": 2, "U8": 1,
         "BOOL": 1, "F8_E4M3": 1, "F8_E5M2": 1}

def check(header):
    """Raise ValueError unless the offsets tile the data section."""
    end = 0
    for name in sorted(header, key=lambda k: header[k]["data_offsets"]):
        t = header[name]
        b, e = t["data_offsets"]
        count = 1
        for d in t["shape"]:
            count *= d
        if e - b != SIZES[t["dtype"]] * count:           # step S4
            raise ValueError(f"{name}: size does not match the shape")
        if b != end:
            raise ValueError(f"{name}: gap or overlap at byte {end}")
        end = e
    return end                      # the length of the data section

src = sys.argv[1]
(n,) = struct.unpack("<Q", read(src, 0, 8))
h = json.loads(read(src, 8, n)); h.pop("__metadata__", None)
print(check(h))
h["model.norm.weight"]["shape"] = [575]
try:
    check(h)
except ValueError as err:
    print("caught:", err)
