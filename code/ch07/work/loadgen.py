# loadgen.py -- time to first token and inter-token gaps of a server
import json, statistics, sys, threading, time, urllib.request

URL = sys.argv[1] + "/chat/completions"     # e.g. http://127.0.0.1:8080/v1
N, C = int(sys.argv[2]), int(sys.argv[3])   # requests, concurrency
BODY = json.dumps({"model": "default", "stream": True, "max_tokens": 128,
    "messages": [{"role": "user", "content": "Count to fifty."}]}).encode()
lock, ttft, gaps, out, left = threading.Lock(), [], [], [0], [N]
TEXT = ("content", "reasoning_content", "reasoning")   # answer, thinking

def one():
    req = urllib.request.Request(URL, BODY,
                                 {"Content-Type": "application/json"})
    t0 = time.perf_counter(); last = None
    with urllib.request.urlopen(req) as resp:
        for line in resp:                    # server-sent events
            if not line.startswith(b"data: ") or b"[DONE]" in line:
                continue
            delta = json.loads(line[6:])["choices"][0]["delta"]
            if not any(delta.get(key) for key in TEXT):
                continue
            now = time.perf_counter()
            with lock:
                if last is None: ttft.append(now - t0)
                else: gaps.append(now - last)
                out[0] += 1
            last = now

def worker():
    while True:
        with lock:
            if left[0] == 0: return
            left[0] -= 1
        one()

start = time.perf_counter()
pool = [threading.Thread(target=worker) for _ in range(C)]
for th in pool: th.start()
for th in pool: th.join()
wall = time.perf_counter() - start
q = lambda v, p: statistics.quantiles(v, n=100)[p - 1] * 1000
print(f"{N / wall:.2f} requests/s, {out[0] / wall:.1f} chunks/s")
print(f"TTFT ms: p50 {q(ttft, 50):.1f}  p90 {q(ttft, 90):.1f}")
print(f"gap  ms: p50 {q(gaps, 50):.1f}  p99 {q(gaps, 99):.1f}")
