# st_tensor.py -- print the first values of one tensor (Algorithm S)
import json, struct, sys
from st_header_lib import read        # the read() function shown above

def decode(raw, dtype):
    """Little-endian bytes -> list of Python floats."""
    if dtype == "F32":
        return list(struct.unpack(f"<{len(raw) // 4}f", raw))
    if dtype == "F16":
        return list(struct.unpack(f"<{len(raw) // 2}e", raw))
    if dtype == "BF16":                  # upper half of a float32
        u16 = struct.unpack(f"<{len(raw) // 2}H", raw)
        return [struct.unpack("<f", struct.pack("<I", u << 16))[0]
                for u in u16]
    raise ValueError(f"dtype {dtype} not handled here")

src, name, k = sys.argv[1], sys.argv[2], int(sys.argv[3])
(n,) = struct.unpack("<Q", read(src, 0, 8))         # S1
t = json.loads(read(src, 8, n))[name]                # S2, S3
begin, end = t["data_offsets"]
size = {"F32": 4, "F16": 2, "BF16": 2}[t["dtype"]]
count = min(k, (end - begin) // size)
raw = read(src, 8 + n + begin, count * size)         # S5
print(name, t["dtype"], t["shape"], decode(raw, t["dtype"]))  # S6
