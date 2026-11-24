"""matmul.py -- multiply two matrices by hand and with NumPy, then time
the products of one feed-forward projection of Qwen3-1.7B for decoding
(one row) and for prompt processing (512 rows).

Usage: python3 matmul.py         (needs NumPy)
"""
import time
import numpy as np

def matmul(a, b):
    """Rows of a times columns of b: (m x k)(k x n) = (m x n)."""
    cols = list(zip(*b))
    return [[sum(x * y for x, y in zip(row, col)) for col in cols]
            for row in a]

def best(f, repeat):
    """The shortest of several runs of f(), in seconds."""
    times = []
    for _ in range(repeat):
        t = time.perf_counter()
        f()
        times.append(time.perf_counter() - t)
    return min(times)

rng = np.random.default_rng(1)
n = 128
A = rng.standard_normal((n, n), dtype=np.float32)
B = rng.standard_normal((n, n), dtype=np.float32)
a, b = A.tolist(), B.tolist()
assert np.allclose(np.array(matmul(a, b)), A @ B, atol=1e-3)
for name, f, r in (("Python loops", lambda: matmul(a, b), 3),
                   ("NumPy @", lambda: A @ B, 200)):
    t = best(f, r)
    print(f"{name:12s} {n}x{n}x{n}: {t * 1e3:9.3f} ms"
          f" {2 * n**3 / t / 1e9:9.2f} GFLOP/s")

# Eight copies of one projection, d x d_ff = 2048 x 6144 in FP32: 400 MB,
# more than any cache of the machine, as the layers of a model are.
d, dff, layers = 2048, 6144, 8
Ws = [rng.standard_normal((d, dff), dtype=np.float32)
      for _ in range(layers)]
for rows in (1, 512):
    X = rng.standard_normal((rows, d), dtype=np.float32)
    t = best(lambda: [X @ W for W in Ws], 10) / layers
    flops = 2 * rows * d * dff
    nbytes = 4 * (d * dff + rows * d + rows * dff)
    print(f"({rows:3d} x {d})({d} x {dff}): {t * 1e3:7.3f} ms"
          f" {flops / t / 1e9:7.1f} GFLOP/s {nbytes / t / 1e9:5.1f} GB/s"
          f" I = {flops / nbytes:5.1f}")
