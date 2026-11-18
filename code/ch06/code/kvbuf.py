# kvbuf.py MODEL [OPTIONS] -- start llama-server with one slot and a
# context of 4096 tokens, print the buffers of the KV cache that it
# allocates, and stop it again.
import re, subprocess, sys

PAT = re.compile(r"llama_kv_cache: size = *([\d.]+) MiB \( *(\d+) cells, *"
                 r"(\d+) layers.*K \((\w+)\).*V \((\w+)\)")
cmd = ["llama-server", "-hf", sys.argv[1], "-c", "4096", "-np", "1",
       "-lv", "4"] + sys.argv[2:]           # -lv 4: with trace messages
with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                      text=True, errors="replace") as server:
    for line in server.stdout:
        m = PAT.search(line)
        if m:
            mib, cells, layers, k, v = m.groups()
            print(f"{layers:>2} layers x {cells:>5} positions  "
                  f"K {k:<5} V {v:<5} {mib:>8} MiB")
        if "listening on" in line:
            server.terminate()
