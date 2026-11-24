#!/usr/bin/env python3
"""Median wall time of a command over N runs (Chapter 16).

usage: timeit.py N COMMAND...
"""
import statistics
import subprocess
import sys
import time

n, command = int(sys.argv[1]), sys.argv[2:]
times = []
for _ in range(n):
    start = time.perf_counter()
    subprocess.run(command, stdout=subprocess.DEVNULL, check=True)
    times.append(time.perf_counter() - start)
print(f"   median of {n} starts: {1000 * statistics.median(times):.1f} ms")
