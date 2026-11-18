#!/usr/bin/env python3
"""mmap_pagein.py -- what it costs to touch a page of a memory-mapped model
file, warm (pages already in the page cache) and cold (evicted first).

    python3 mmap_pagein.py FILE [-k 2000]

Maps FILE read-only and reads one byte from each of K pages chosen at
random, timing every read; prints the median and the 10th and 90th
percentiles in microseconds. Three cases: cold (pages evicted first, so
each read waits for the disk), warm (pages in the page cache but not yet
in this mapping, so each read takes a minor fault) and hot (pages already
mapped). Cold reads need pages that are not cached: on Linux
posix_fadvise(DONTNEED) evicts them without privileges; on macOS the
script times a copy of FILE written with F_NOCACHE beside it (and then
deleted); elsewhere the cold case is skipped. The mapping is advised
MADV_RANDOM, so that a cold fault reads one page and no read-ahead hides
the cost of the next; without it Linux read 3 to 4 ms around each early
fault and had the whole file in memory after a few hundred faults.
"""
import argparse, mmap, os, platform, random, statistics, sys, time


def pct(v, q):
    v = sorted(v)
    return v[min(len(v) - 1, int(q * len(v)))]


def advise_random(m):
    if hasattr(m, "madvise") and hasattr(mmap, "MADV_RANDOM"):
        m.madvise(mmap.MADV_RANDOM)


def touch(m, offsets):
    advise_random(m)
    out = []
    for o in offsets:
        t = time.perf_counter_ns()
        m[o]
        out.append((time.perf_counter_ns() - t) / 1000)
    return out


def cold_copy_darwin(path, offsets):
    """Copy PATH with F_NOCACHE writes, so none of its pages is cached."""
    import fcntl
    tmp = path + ".nocache-copy"
    src = open(path, "rb")
    dst = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    fcntl.fcntl(dst, fcntl.F_NOCACHE, 1)
    while chunk := src.read(1 << 24):
        os.write(dst, chunk)
    os.fsync(dst); os.close(dst); src.close()
    fd = os.open(tmp, os.O_RDONLY)
    m = mmap.mmap(fd, 0, access=mmap.ACCESS_READ)
    v = touch(m, offsets)
    m.close(); os.close(fd); os.unlink(tmp)
    return v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("-k", type=int, default=2000)
    a = ap.parse_args()
    size = os.path.getsize(a.file)
    page = mmap.PAGESIZE
    rng = random.Random(1)
    offsets = [rng.randrange(size // page) * page for _ in range(a.k)]
    fd = os.open(a.file, os.O_RDONLY | getattr(os, "O_BINARY", 0))
    print(f"# {platform.node()} {platform.platform()} page {page} B, "
          f"file {size / 2**30:.2f} GiB, {a.k} random pages, "
          f"{time.strftime('%Y-%m-%dT%H:%M:%S%z')}")
    print("case,n,median_us,p10_us,p90_us")
    cases = []
    if hasattr(os, "posix_fadvise") or sys.platform == "darwin":
        cases.append("cold")
    cases += ["warm", "hot"]
    for case in cases:
        if case == "cold" and sys.platform == "darwin":
            v = cold_copy_darwin(a.file, offsets)
            print(f"cold,{len(v)},{statistics.median(v):.3f},"
                  f"{pct(v, 0.1):.3f},{pct(v, 0.9):.3f}")
            continue
        if case == "cold":
            os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
        else:                          # make sure the pages are cached
            for o in offsets:
                if hasattr(os, "pread"):
                    os.pread(fd, 1, o)
                else:                  # Windows
                    os.lseek(fd, o, os.SEEK_SET); os.read(fd, 1)
        m = mmap.mmap(fd, 0, access=mmap.ACCESS_READ)
        if case == "hot":
            touch(m, offsets)          # map them in, then time
        v = touch(m, offsets)
        print(f"{case},{len(v)},{statistics.median(v):.3f},"
              f"{pct(v, 0.1):.3f},{pct(v, 0.9):.3f}")
        m.close()
    os.close(fd)


if __name__ == "__main__":
    main()
