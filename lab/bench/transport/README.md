# Transport round trips (Figure 1.5)

Measurements behind Figure 1.5 of Chapter 1: the time of one
round trip of a 64-byte message over each transport that the stack uses
between its building blocks, and the time to touch one page of a
memory-mapped model file.

| File | What it does |
|---|---|
| `rtt.py` | Echo round trips from Python: function call, ctypes, shared memory, stdio pipe to a child, Unix socket, `multiprocessing.connection` (Unix socket; a named pipe on Windows), loopback TCP, ZeroMQ REQ/REP over `ipc://` and `tcp://`, HTTP/1.1 with keep-alive and with a one-event SSE response, D-Bus `Peer.Ping` (Linux, `jeepney`), `GET /health` of llama-server and `GET /api/version` of Ollama if they run, LAN echo (`--serve` on one host, `--remote` on another) and kept-alive HTTPS to two public hosts (`--internet N`) |
| `xpc_rtt.swift` | XPC round trip on macOS: `NSXPCConnection` to an anonymous listener |
| `mmap_pagein.py` | One byte from each of 2000 random pages of a GGUF file: cold (evicted, `MADV_RANDOM`), warm (cached, a minor fault) and hot (mapped) |
| `run_linux.sh`, `run_mac.py` | Run the above on a shared lab machine: wait for the other workload's lock, hold it during the run |
| `mkfig.py` | Write the rows of `figures/transports.tex` and `summary.md` from `results/` |

Each test makes 200 untimed round trips and then 5000 timed ones (2000
pages for `mmap_pagein.py`, 20 requests spaced 0.2 s apart for HTTPS) and
reports the median and the 10th and 90th percentiles in microseconds.
Calls shorter than a microsecond are timed in batches of 1000.

```sh
python3 -m venv venv && venv/bin/pip install pyzmq jeepney   # jeepney: Linux
venv/bin/python rtt.py -n 5000 > results/$(hostname -s)-rtt.csv
venv/bin/python mmap_pagein.py MODEL.gguf > results/$(hostname -s)-mmap.csv
swiftc -O xpc_rtt.swift -o xpc_rtt && ./xpc_rtt 5000          # macOS
# LAN: on host A
venv/bin/python rtt.py --serve tcp 0.0.0.0:47001 &
venv/bin/python rtt.py --serve http 0.0.0.0:47002 &
# on host B
venv/bin/python rtt.py -n 5000 --remote A:47001:47002 > results/B-lan.csv
python3 mkfig.py results BOOK/figures/transports.tex   # in the book's sources
```

Everything is measured from Python, which is how most of the stack's glue
(MCP SDKs, vLLM, SGLang, agent frameworks) sees these transports; a C
program would see shorter times for the fastest rows. The PCIe and NVLink
rows come from `lab/bench/gpu` on `kr0m-gpu` (S5-CloudGPU), recorded in
`results/kr0m-gpu-rtt.csv`.

Notes from the runs (2026-11-14):

- Inbound connections to the lab Mac were slow (TCP echo median 4.9 ms,
  ping 4 to 318 ms) while its outbound traffic was normal, so the LAN
  rows come from two Linux machines on the same switch, krom2 (client)
  and xps-8930 (server). krom2's firewall refuses inbound connections on
  high ports.
- Without `MADV_RANDOM`, Linux read 3 to 4 ms around each of the first
  faults of a cold mapping and held the whole 0.7 GB file after about 240
  of the 2000 faults, so most "cold" reads were really warm.
- The Windows machine reaches the LAN through a Hyper-V virtual switch
  and was not used for the LAN rows. Python offers no `madvise` and no
  way to evict a file's pages there, so its mmap results have no cold
  case and its warm case keeps Windows' own fault clustering.
- The lab machines also run another workload; the runners waited for its
  locks and held them while measuring (the Mac at a falling one-minute
  load of 8, xps-8930 at 0.3 and krom2 at 3.2, the latter still falling
  from that workload's last job).
