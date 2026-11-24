# write a tiny safetensors file: a BF16 2x3 matrix and an F32 vector
import json, struct, sys
def bf16(x):
    return struct.pack("<I", struct.unpack("<I", struct.pack("<f", x))[0])[2:]
a = b"".join(bf16(v) for v in [1.0, 2.0, 3.0, -1.5, 0.5, 4.0])
v = struct.pack("<3f", 0.25, 0.5, 0.75)
hdr = {"__metadata__": {"format": "pt"},
       "a.weight": {"dtype": "BF16", "shape": [2, 3], "data_offsets": [0, 12]},
       "b.bias": {"dtype": "F32", "shape": [3], "data_offsets": [12, 24]}}
h = json.dumps(hdr).encode(); h += b" " * ((8 - len(h) % 8) % 8)
open(sys.argv[1], "wb").write(struct.pack("<Q", len(h)) + h + a + v)
