# splits.py -- show how ggml's scheduler (Algorithm H) divided a graph.
# Runs llama-completion for two tokens with GGML_SCHED_DEBUG=2 and prints
# the splits of the last graph, a decoding step of one token: backend,
# nodes (views are left out), first and last node, and the tensors copied
# in before the split starts, with their sizes as ggml prints them
# (rounded down to KiB or MiB). Splits are numbered from 1, as in the book.
#
# Usage: python3 splits.py MODEL.gguf [llama-completion options]
#   e.g. python3 splits.py model.gguf -ngl 28
import os, re, subprocess, sys

STAMP = re.compile(r"\d+\.\d+\.\d+\.\d+ [DIWE] ")
SPLIT = re.compile(r"## SPLIT #(\d+): (\S+) # (\d+) inputs:?(.*)")
NODE = re.compile(r"node #\s*\d+ \(\s*\w+\):\s+(.*?) \(\s*\d+[KM]\) \[")
INPUT = re.compile(r"\[(.*?) \(\s*(\d+[KM])\)\]")

def run(model, options):
    cmd = ["llama-completion", "-m", model, "-p", "Hello", "-n", "2",
           "-no-cnv", "--no-warmup", "-v"] + options
    env = dict(os.environ, GGML_SCHED_DEBUG="2")
    p = subprocess.run(cmd, env=env, stdin=subprocess.DEVNULL,
                       capture_output=True, text=True, errors="replace")
    return STAMP.sub("", p.stdout + p.stderr).splitlines()

def graphs(lines):
    out = []
    for line in lines:
        m = SPLIT.match(line)
        if m:
            if m.group(1) == "0":
                out.append([])                  # a new graph begins
            out[-1].append(dict(backend=m.group(2), nodes=[],
                                copies=INPUT.findall(m.group(4))))
            continue
        m = NODE.match(line)
        if m and out:
            out[-1][-1]["nodes"].append(m.group(1).strip())
    return out

if __name__ == "__main__":
    last = graphs(run(sys.argv[1], sys.argv[2:]))[-1]
    for i, s in enumerate(last, 1):
        n = s["nodes"]
        span = n[0] if len(n) == 1 else f"{n[0]} .. {n[-1]}"
        unit = "node" if len(n) == 1 else "nodes"
        print(f"split {i}: {s['backend']}, {len(n)} {unit}, {span}")
        for name, size in s["copies"]:
            size = "<1K" if size == "0K" else size
            print(f"    copy in: {name} ({size})")
