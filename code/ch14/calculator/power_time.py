"""power_time.py: how long CPython takes to compute 9 ** (9 ** e).

  python3 power_time.py 6 7 8
Answer 14.1 extrapolates from these times to 9 ** 9 ** 9.
"""
import sys, time
for e in map(int, sys.argv[1:]):
    t = time.perf_counter()
    x = 9 ** (9 ** e)
    dt = time.perf_counter() - t
    print("9**(9**%d): %d bits, %.2f s" % (e, x.bit_length(), dt), flush=True)
print(sys.version.split()[0])
