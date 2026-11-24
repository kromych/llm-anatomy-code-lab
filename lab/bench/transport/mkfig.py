#!/usr/bin/env python3
"""mkfig.py -- write the rows of the figure of transports
(figures/transports.tex, in the overview chapter) from the
measurements in results/.

    python3 mkfig.py [RESULTS [FIGURE]]

Each row of the figure gets the median of every measurement that belongs
to it, on every machine: a dark bar spans the smallest and the largest of
these medians and a dot marks each one. Rows that the lab cannot measure
keep a light bar, an estimate from vendor specifications. RESULTS is the
directory results/ beside this script unless given. With FIGURE, the file
figures/transports.tex of the book's sources, the script replaces the text
between the lines '% BEGIN ROWS' and '% END ROWS' of the figure; in either
case it writes a summary table of all medians (summary.md, beside the
script).
"""
import csv, glob, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RES = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "results")
FIG = sys.argv[2] if len(sys.argv) > 2 else None

MACHINES = {"krom1u": "Apple M1 Ultra, macOS 27.2",
            "xps-8930": "Core i7-8700, Fedora 44",
            "krom2": "Apple M2, Fedora Asahi 44",
            "kromyrzen": "Ryzen 7 3700X, Windows 11",
            "kr0m-gpu": "8 x NVIDIA H100 PCIe, Ubuntu 24.04"}

# (group, label, where, tests, estimate (log10 s) or None, note)
ROWS = [
    ("Inside one process", None, None, None, None, None),
    (None, "Function call, FFI",
     "harness and its agent loop; agent and Transformers or "
     "llama-cpp-python",
     ["call", "ctypes"], None, None),
    (None, "A page of a mapped\\\\model file",
     "engine reading its weights: page mapped, in the page cache, "
     "or on the SSD", ["mmap-hot", "mmap-warm", "mmap-cold"], None, None),
    ("Between processes on one machine", None, None, None, None, None),
    (None, "Shared memory",
     "vLLM broadcasting inputs to its GPU worker processes",
     ["shm"], None, None),
    (None, "Pipes and stdio",
     "MCP servers over stdio; Agent Client Protocol; tool subprocesses",
     ["stdio"], None, None),
    (None, "Unix or TCP socket,\\\\named pipe, ZeroMQ",
     "vLLM and SGLang between front end and engine core; Docker Engine API",
     ["unix", "mpconn", "tcp", "zmq-ipc", "zmq-tcp"], None, None),
    (None, "XPC, COM/ALPC, D-Bus",
     "OS-native IPC to system services and privileged helpers "
     "(macOS, Windows, Linux)", ["xpc", "dbus"], (-5, -3), None),
    (None, "HTTP on loopback,\\\\with SSE",
     "local OpenAI-compatible servers; Ollama's and LM Studio's servers "
     "and their runners; MCP over HTTP",
     ["http", "sse", "llama-server", "ollama"], None, None),
    ("Across the network", None, None, None, None, None),
    (None, "TCP and HTTP in a LAN",
     "a GPU server down the hall; Triton Inference Server",
     ["lan-tcp", "lan-http"], None, None),
    (None, "HTTPS over the Internet",
     "hosted model APIs; remote MCP servers", ["https"], None, None),
    ("To and between accelerators", None, None, None, None, None),
    (None, "PCIe DMA",
     "CPU to discrete GPU: upload weights, offload layers, or KV cache; "
     "\\qty{64}{GB/s} each way for PCIe 5.0 x16", ["pcie-4k"], None, None),
    (None, "Unified memory",
     "Apple silicon, AMD Ryzen AI Max, NVIDIA GB10: CPU and GPU share one "
     "memory", None, None, "no copy at all"),
    (None, "NVLink, Infinity Fabric,\\\\RDMA",
     "tensor-parallel all-reduce across GPUs and nodes; NVLink "
     "up to \\qty{900}{GB/s} each way", ["allreduce-pair"], None, None),
]


def load():
    """{(test, host): median_us}"""
    m = {}
    for f in sorted(glob.glob(os.path.join(RES, "*.csv"))):
        host = os.path.basename(f).split("-")[0]
        for dashed in ("xps-8930", "kr0m-gpu"):
            if os.path.basename(f).startswith(dashed):
                host = dashed
        kind = "mmap" if f.endswith("-mmap.csv") else "rtt"
        for r in csv.reader(l for l in open(f) if not l.startswith("#")):
            if not r or r[0] in ("test", "case"):
                continue
            name = ("mmap-" + r[0]) if kind == "mmap" else r[0]
            if name.startswith("https-"):
                name = "https"
                key = (name, host + ":" + r[0])
            else:
                key = (name, host)
            m[key] = float(r[2])
    return m


def height(label, where):
    """Height of a row in cm: for one line, for a description of two
    lines (it wraps past some 58 characters), for a label of two."""
    if "\\\\" in label:
        return 0.84
    plain = re.sub(r"\\[a-zA-Z]+|[{}]", "", where)
    return 0.76 if len(plain) > 58 else 0.6


def main():
    m = load()
    out, y = [], -0.2     # y of a group's title, then the upper edge of a row
    summary = ["| row | test | machine | median |", "|---|---|---|---|"]
    for group, label, where, tests, est, note in ROWS:
        if group:
            if out:
                y -= 0.33
            out.append(f"  \\group{{{y:.2f}}}{{{group}}}")
            y -= 0.25
            continue
        vals = []
        for (t, h), v in sorted(m.items()):
            if tests and t in tests:
                vals.append(math.log10(v * 1e-6))
                summary.append(f"| {label.replace(chr(92)*2, ' ')} | {t} | "
                               f"{h} | {v:g} us |")
        lo = f"{min(vals):.3f}" if vals else "0"
        hi = f"{max(vals):.3f}" if vals else "0"
        dots = ",".join(f"{v:.3f}" for v in vals)
        elo, ehi = est if est else (0, 0)
        step = height(label, where)
        c = y - step / 2      # the row stands in the middle of its height
        out.append(f"  \\trow{{{c:.2f}}}{{{label}}}\n    {{{where}}}"
                   f"\n    {{{elo}}}{{{ehi}}}{{{lo}}}{{{hi}}}{{{dots}}}")
        if note:
            out.append(f"  \\node[tinynote, plate, anchor=west] at "
                       f"({{\\AX+0.1}},{c:.2f}) {{{note}}};")
        y -= step
        out.append(f"  \\sep{{{y:.2f}}}")
    out.append(f"  \\def\\Bot{{{y - 0.11:.2f}}}")
    block = "\n".join(out)
    if FIG:
        src = open(FIG).read()
        a = src.index("% BEGIN ROWS")
        b = src.index("% END ROWS")
        src = src[:a] + "% BEGIN ROWS (written by lab/bench/transport/mkfig.py)\n" \
            + block + "\n  " + src[b:]
        open(FIG, "w").write(src)
    with open(os.path.join(HERE, "summary.md"), "w") as f:
        f.write("# Round trips measured for figures/transports.tex\n\n")
        f.write("Median of each test, in microseconds; raw files in "
                "results/. Machines:\n\n")
        for h, d in MACHINES.items():
            f.write(f"- {h}: {d}\n")
        f.write("\n" + "\n".join(summary) + "\n")
    print(f"{len(m)} medians; "
          + (f"figure rows written, Bot={y - 0.11:.2f}" if FIG
             else "no figure given, summary.md alone written"))


if __name__ == "__main__":
    main()
