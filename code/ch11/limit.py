# limit.py -- run a tool in a child process that is killed after a time.
import multiprocessing as mp, queue, time

def child(fn, args, q):
    try:
        q.put(("ok", str(fn(**args))))
    except Exception as e:
        q.put(("error", f"{type(e).__name__}: {e}"))

def call_with_limit(fn, args, seconds):
    q = mp.Queue()
    p = mp.Process(target=child, args=(fn, args, q))
    p.start()
    try:
        kind, text = q.get(timeout=seconds)  # read before join: a large
    except queue.Empty:                      # result would block the child
        p.terminate()
        p.join()
        return f"error: {fn.__name__} took longer than {seconds} s"
    p.join()
    return text if kind == "ok" else "error: " + text

def slow(n: int) -> int:
    time.sleep(n)
    return n

if __name__ == "__main__":
    for n, limit in [(0, 3), (1, 3), (10, 2)]:
        t = time.time()
        out = call_with_limit(slow, {"n": n}, limit)
        print(f"slow({n}), limit {limit} s: {out} after "
              f"{time.time() - t:.2f} s")
