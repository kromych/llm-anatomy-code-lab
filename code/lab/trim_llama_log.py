"""Trim a llama-server -lv 4 log to the lines relevant for the book appendix.
Usage: python3 -I trim_llama_log.py <in> <out> <header-line>"""
import re, sys
src, dst, header = sys.argv[1], sys.argv[2], sys.argv[3]
lines = open(src, errors="replace").read().replace("\r", "\n").split("\n")
keep = re.compile(
    r"device_info|  - (CPU|Vulkan)|system_info|n_parallel|without SSL|threads for HTTP|security:|"
    r"load_model: (loading|local path|initializing|prompt cache)|memory breakdown|  - (Host|CPU_REPACK|Vulkan)|"
    r"projected to use|ggml_vulkan|vulkan|Vulkan|"
    r"print_info: (arch|file type|file size|model type|model params|n_ctx_train|general.name)|"
    r"load_tensors: (offload|offloaded|loading model tensors)|"
    r"llama_context: (n_seq_max|n_ctx |n_batch|n_ubatch|flash_attn|kv_unified)|"
    r"llama_kv_cache: size|Flash Attention enabled|compute buffer size|graph: nodes|threadpool init|"
    r"warming up|n_slots|chat template, thinking|model loaded|listening on|print_timing|cleaning up|"
    r"control-looking token|W srv|E srv"
)
out, mapped = [header], []
for ln in lines:
    m = re.search(r"(\S+) model buffer size =\s+([\d.]+) MiB", ln)
    if m and "load_tensors" in ln:
        mapped.append((m.group(1), float(m.group(2))))
        continue
    if keep.search(ln):
        out.append(ln[:240])
if mapped:
    agg = {}
    for name, size in mapped:
        n, s = agg.get(name, (0, 0.0)); agg[name] = (n + 1, s + size)
    out.append("[trimmed] load_tensors model buffers: " +
               ", ".join(f"{k} {n} buffers totalling {s:.2f} MiB" for k, (n, s) in agg.items()))
open(dst, "w").write("\n".join(out) + "\n")
print(dst, len(out), "lines")
