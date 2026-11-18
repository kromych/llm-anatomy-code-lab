import time, multiprocessing as mp, limit, big_tool
def join_first(fn, args, seconds):
    q = mp.Queue(); p = mp.Process(target=limit.child, args=(fn, args, q)); p.start(); p.join(seconds)
    if p.is_alive():
        p.terminate(); p.join(); return "timed out"
    return q.get()[1]
if __name__ == "__main__":
    t = time.time(); r = limit.call_with_limit(big_tool.big, {"n": 1_000_000}, 3); print("new", len(r), round(time.time() - t, 2))
    t = time.time(); r = join_first(big_tool.big, {"n": 1_000_000}, 3); print("join-first", r if len(r) < 20 else len(r), round(time.time() - t, 2))
