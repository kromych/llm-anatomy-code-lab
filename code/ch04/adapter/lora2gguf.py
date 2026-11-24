# lora2gguf.py ADAPTER_DIR OUT.gguf -- the adapter that PEFT wrote, as the
# GGUF file that llama.cpp loads with --lora (standard library only).
import json, re, struct, sys

GGUF = {"q_proj": "attn_q", "k_proj": "attn_k", "v_proj": "attn_v",
        "o_proj": "attn_output", "gate_proj": "ffn_gate",
        "up_proj": "ffn_up", "down_proj": "ffn_down"}
ALIGN = 32

def gstr(s):
    return struct.pack("<Q", len(s)) + s.encode()

def text(key, value):                    # a key with a string, type 8
    return gstr(key) + struct.pack("<I", 8) + gstr(value)

config = json.load(open(sys.argv[1] + "/adapter_config.json"))
with open(sys.argv[1] + "/adapter_model.safetensors", "rb") as f:
    (n,) = struct.unpack("<Q", f.read(8))
    header, data = json.loads(f.read(n)), f.read()

tensors = []                             # (name, dimensions, bytes)
PEFT = re.compile(r"layers\.(\d+)\.\w+\.(\w+)\.lora_([AB])\.weight$")
for name, t in header.items():           # ...layers.0.self_attn.q_proj.
    m = PEFT.search(name)                # lora_A.weight
    if m:
        assert t["dtype"] == "F32"
        begin, end = t["data_offsets"]
        layer, matrix, which = m[1], GGUF[m[2]], m[3].lower()
        tensors.append((f"blk.{layer}.{matrix}.weight.lora_{which}",
                        t["shape"][::-1], data[begin:end]))

kv = [text("general.architecture", "llama"),
      text("general.type", "adapter"), text("adapter.type", "lora"),
      gstr("adapter.lora.alpha")
      + struct.pack("<If", 6, config["lora_alpha"])]
infos, offset = [], 0
for name, dims, raw in tensors:
    infos.append(gstr(name) + struct.pack(f"<I{len(dims)}QIQ", len(dims),
                                          *dims, 0, offset))
    offset += len(raw) + -len(raw) % ALIGN
head = (b"GGUF" + struct.pack("<IQQ", 3, len(tensors), len(kv))
        + b"".join(kv) + b"".join(infos))
with open(sys.argv[2], "wb") as f:
    f.write(head + b"\0" * (-len(head) % ALIGN))
    for name, dims, raw in tensors:
        f.write(raw + b"\0" * (-len(raw) % ALIGN))
print(f"{len(tensors)} tensors, rank {config['r']}, "
      f"alpha {config['lora_alpha']}: {sys.argv[2]}")
