# service.py MODEL.gguf [PORT [SLOTS]] -- a server in service: the moment
# it is ready, a full house, sleeping on idle, and several models behind
# one address.  Starts and stops llama-server itself; standard library.
import contextlib, json, subprocess, sys, threading, time, urllib.request

MODEL = sys.argv[1]
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8109
SLOTS = sys.argv[3] if len(sys.argv) > 3 else "2"
BASE = f"http://127.0.0.1:{PORT}"

def get(path):
    with urllib.request.urlopen(BASE + path, timeout=5) as resp:
        return resp.status, resp.read().decode()

def chat(model=None, tokens=40, give_up=None):
    """One streamed request; seconds to the first token and to the end,
    or None for a client that gave up after GIVE_UP seconds."""
    body = {"messages": [{"role": "user", "content": "Count upward."}],
            "max_tokens": tokens, "stream": True, "temperature": 0,
            "chat_template_kwargs": {"enable_thinking": False}}
    if model:
        body["model"] = model
    req = urllib.request.Request(BASE + "/v1/chat/completions",
                                 json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    t0, first = time.time(), None
    try:
        with urllib.request.urlopen(req, timeout=give_up or 300) as resp:
            for line in resp:
                if first is None and line.startswith(b"data: {"):
                    first = time.time() - t0
    except OSError:
        return None
    return first, time.time() - t0

def metric(name):
    for line in get("/metrics")[1].splitlines():
        if line.startswith("llamacpp:" + name + " "):
            return float(line.split()[1])

@contextlib.contextmanager
def server(options):
    child = subprocess.Popen(
        ["llama-server", "--host", "127.0.0.1", "--port", str(PORT)]
        + options, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        yield child
    finally:
        child.terminate()
        child.wait()

def rss(child):                          # mebibytes of resident memory
    out = subprocess.run(["ps", "-o", "rss=", "-p", str(child.pid)],
                         capture_output=True, text=True).stdout
    return int(out) // 1024

with server(["-m", MODEL, "-np", SLOTS, "--metrics",
             "--sleep-idle-seconds", "5"]) as child:
    t0, seen = time.time(), {}           # status -> first and last time
    while 200 not in seen:
        try:
            status = get("/health")[0]
        except urllib.error.HTTPError as e:
            status = e.code
        except OSError:
            status = "no listener"
        seen.setdefault(status, [time.time() - t0])
        seen[status][1:] = [time.time() - t0]
        time.sleep(0.01)
    print("readiness, seconds after the start:")
    for status, (a, b) in seen.items():
        print(f"  /health {status}: from {a:.2f} to {b:.2f}")

    print(f"six requests at once for {SLOTS} slots, 40 tokens each:")
    results, deferred = [None] * 6, []
    def one(i):
        results[i] = chat()
    threads = [threading.Thread(target=one, args=(i,)) for i in range(6)]
    for t in threads:
        t.start()
    time.sleep(0.3)
    deferred.append(metric("requests_deferred"))
    quitter = chat(give_up=0.2)          # a seventh, impatient client
    for t in threads:
        t.join()
    for first, total in sorted(results):
        print(f"  first token after {first:5.2f} s, done after "
              f"{total:5.2f} s")
    print(f"  deferred while they ran: {deferred[0]:.0f}")
    print("  the client with 0.2 s of patience got", "nothing" if
          quitter is None else f"an answer after {quitter[1]:.2f} s")
    print(f"  tokens generated in all: "
          f"{metric('tokens_predicted_total'):.0f}")

    print("sleeping on idle (--sleep-idle-seconds 5):")
    awake, t0 = rss(child), time.time()
    while not json.loads(get("/props")[1])["is_sleeping"]:
        get("/health")                   # neither question counts as work
        time.sleep(0.5)
    asleep, nap = rss(child), time.time() - t0
    health = get("/health")[0]
    still = json.loads(get("/props")[1])["is_sleeping"]
    first, total = chat(tokens=8)
    print(f"  resident memory {awake} MiB awake, {asleep} MiB asleep")
    print(f"  asleep after {nap:.1f} s of questions to /health and /props")
    print(f"  /health then answers {health}; still asleep: {still}")
    print(f"  the request that wakes the server: first token after "
          f"{first:.2f} s")
    first, total = chat(tokens=8)
    print(f"  the request after it: {first:.2f} s")

print("a router with room for one model (--models-max 1):")
with server(["--models-max", "1"]):
    while True:
        try:
            names = [m["id"] for m in json.loads(get("/models")[1])["data"]]
            break
        except OSError:
            time.sleep(0.05)
    small = [n for n in names if "1.7B" in n or "gemma-3-1b" in n]
    print(f"  {len(names)} models in the cache; we ask for two of them")
    for name in (small[0], small[0], small[1], small[1], small[0]):
        first, total = chat(model=name, tokens=8)
        print(f"  {name.split('/')[1]:28} first token after {first:.2f} s")
