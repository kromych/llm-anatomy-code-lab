# tiled.py -- Algorithm M: blocked matrix multiply with a count of the
# words moved between slow and fast memory (standard library only).
import random

def matmul_tiled(A, B, mt, nt, kt):
    m, k, n = len(A), len(A[0]), len(B[0])
    C = [[0.0] * n for _ in range(m)]
    loads = stores = 0
    for i0 in range(0, m, mt):                  # M1: each tile of C
        for j0 in range(0, n, nt):
            acc = [[0.0] * min(nt, n - j0)      # M2: accumulator
                   for _ in range(min(mt, m - i0))]
            for p0 in range(0, k, kt):          # M3: one k-step
                a = [row[p0:p0 + kt] for row in A[i0:i0 + mt]]
                b = [row[j0:j0 + nt] for row in B[p0:p0 + kt]]
                loads += sum(map(len, a)) + sum(map(len, b))
                for i, arow in enumerate(a):    # M4: multiply-add
                    crow = acc[i]
                    for p, x in enumerate(arow):
                        brow = b[p]
                        for j in range(len(brow)):
                            crow[j] += x * brow[j]
            for i, crow in enumerate(acc):      # M5: write the tile
                C[i0 + i][j0:j0 + len(crow)] = crow
                stores += len(crow)
    return C, loads, stores

if __name__ == "__main__":
    random.seed(1)
    m = n = k = 96
    A = [[random.random() for _ in range(k)] for _ in range(m)]
    B = [[random.random() for _ in range(n)] for _ in range(k)]
    ref = [[sum(A[i][p] * B[p][j] for p in range(k)) for j in range(n)]
           for i in range(m)]
    flops = 2 * m * n * k
    print(" tile  fast words   words moved   flops/word")
    for t in (1, 4, 8, 16, 32, 48, 96):
        C, ld, st = matmul_tiled(A, B, t, t, t)
        err = max(abs(C[i][j] - ref[i][j])
                  for i in range(m) for j in range(n))
        assert err < 1e-9
        fast = 3 * t * t
        print(f"{t:5d} {fast:11d} {ld + st:13d} {flops / (ld + st):12.1f}")
