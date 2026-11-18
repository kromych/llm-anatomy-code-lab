# coldstart.py -- where the time of a cold start goes: llama-server started
# with an empty or a warm page cache, with memory mapping (the default) and
# without it (--load-mode none), with and without --no-warmup. Prints the
# seconds until the server is ready and from then to the first token of
# the first request. macOS and Linux; no root needed. Further arguments
# go to every start of the server, for instance -ngl 0 to keep the GPU out.
# Usage: python3 coldstart.py FILE.gguf [PORT [RUNS [SERVER_OPTION...]]]
import ctypes, json, mmap, os, subprocess, sys, time, urllib.request

PATH = sys.argv[1]
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8102
RUNS = int(sys.argv[3]) if len(sys.argv) > 3 else 3
EXTRA = sys.argv[4:]
SIZE = os.path.getsize(PATH)
libc = ctypes.CDLL(None, use_errno=True)
libc.mmap.restype = ctypes.c_void_p
libc.mmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int,
                      ctypes.c_int, ctypes.c_int, ctypes.c_longlong]
libc.mincore.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_char_p]
libc.msync.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int]
libc.munmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t]

def page_cache(action):
    """Empty or fill the page cache for the file; return the share of
    its pages that the cache holds afterward."""
    fd = os.open(PATH, os.O_RDONLY)
    addr = libc.mmap(None, SIZE, mmap.PROT_READ, mmap.MAP_SHARED, fd, 0)
    if action == "empty" and hasattr(os, "posix_fadvise"):       # Linux
        os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
    elif action == "empty":                                      # macOS
        libc.msync(addr, SIZE, 2)                        # MS_INVALIDATE
    else:
        t0 = time.time()
        while os.read(fd, 1 << 24):
            pass
        page_cache.seconds = time.time() - t0
    n = (SIZE + mmap.PAGESIZE - 1) // mmap.PAGESIZE
    vec = ctypes.create_string_buffer(n)
    assert libc.mincore(addr, SIZE, vec) == 0
    libc.munmap(addr, SIZE)
    os.close(fd)
    return sum(b & 1 for b in vec.raw) / n

def start(options):
    """Start the server; return the seconds until it is ready and the
    seconds from then to the first token of a request."""
    base = f"http://127.0.0.1:{PORT}"
    t0 = time.time()
    server = subprocess.Popen(
        ["llama-server", "-m", PATH, "--host", "127.0.0.1", "--port",
         str(PORT), "-c", "4096", "-np", "1"] + EXTRA + options,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        while True:
            try:
                urllib.request.urlopen(base + "/health").close()
                break
            except OSError:              # no listener yet, or status 503
                assert server.poll() is None, "the server has exited"
                time.sleep(0.005)
        t1 = time.time()
        body = {"messages": [{"role": "user", "content": "Say hello."}],
                "max_tokens": 8, "stream": True}
        req = urllib.request.Request(base + "/v1/chat/completions",
                                     json.dumps(body).encode(),
                                     {"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            for line in resp:
                if not line.startswith(b"data: {"):
                    continue
                delta = json.loads(line[6:])["choices"][0]["delta"]
                if delta.get("content") or delta.get("reasoning_content"):
                    break
        t2 = time.time()
    finally:
        server.terminate()
        server.wait()
    return t1 - t0, t2 - t1

print(f"{os.path.basename(PATH)}, {SIZE / 1e9:.2f} GB", *EXTRA)
for cache in ["empty", "warm"]:          # a plain read of the file
    page_cache(cache)
    page_cache("warm")
    print(f"read with the page cache {cache}: {page_cache.seconds:.2f} s")
NONE = ["--load-mode", "none"]           # read the file; no mapping
print("page cache  options                       cached  ready  first"
      "    sum")
for cache in ["empty", "warm"]:
    for options in [["--no-warmup"], [], NONE + ["--no-warmup"], NONE]:
        for _ in range(RUNS):
            share = page_cache(cache)
            while cache == "empty" and share > 0.01:    # pages still held
                time.sleep(0.5)                         # by the last run
                share = page_cache(cache)
            ready, first = start(options)
            print(f"{cache:11} {' '.join(options) or '(default)':29} "
                  f"{share:6.2f} {ready:6.2f} {first:6.2f} "
                  f"{ready + first:6.2f}", flush=True)
