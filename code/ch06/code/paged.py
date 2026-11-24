# paged.py -- a paged KV cache with prefix caching (Algorithms P and C).
# It tracks only block numbers and token IDs; no keys or values are kept.
import hashlib
from collections import OrderedDict

def block_hash(prev, tokens):
    return hashlib.sha256(repr((prev, tuple(tokens))).encode()).hexdigest()

class Pool:
    def __init__(self, n_blocks, block_size):
        self.B = block_size
        self.free = OrderedDict.fromkeys(range(n_blocks))  # LRU first
        self.ref = [0] * n_blocks
        self.hash_of = [None] * n_blocks
        self.by_hash = {}                   # hash of full block -> block

    def take(self):                         # step P2: a free block
        if not self.free:
            raise MemoryError("KV cache full: preempt a sequence")
        b, _ = self.free.popitem(last=False)
        if self.hash_of[b] is not None:     # evict its cached contents
            del self.by_hash[self.hash_of[b]]
            self.hash_of[b] = None
        self.ref[b] = 1
        return b

    def share(self, b):
        self.ref[b] += 1
        self.free.pop(b, None)

    def drop(self, b):
        self.ref[b] -= 1
        if self.ref[b] == 0:
            self.free[b] = None             # now most recently used

class Seq:
    def __init__(self, pool):
        self.pool, self.table, self.n = pool, [], 0
        self.h, self.cur = None, []         # last full-block hash, tail

    def prefill(self, tokens):              # Algorithm C, then P
        pool, B, hit = self.pool, self.pool.B, 0
        while hit + B < len(tokens):        # leave a token to compute
            h = block_hash(self.h, tokens[hit:hit + B])
            if h not in pool.by_hash:
                break
            pool.share(pool.by_hash[h])
            self.table.append(pool.by_hash[h])
            self.h, self.n, hit = h, self.n + B, hit + B
        for t in tokens[hit:]:
            self.append(t)
        return hit                          # tokens not recomputed

    def append(self, t):                    # Algorithm P
        pool, B = self.pool, self.pool.B
        if self.n % B == 0:
            self.table.append(pool.take())
            self.cur = []
        elif pool.ref[self.table[-1]] > 1:  # shared tail: copy on write
            old = self.table[-1]
            self.table[-1] = pool.take()
            pool.drop(old)
        self.cur.append(t)
        self.n += 1
        if self.n % B == 0:                 # block full: publish it
            self.h = block_hash(self.h, self.cur)
            b = self.table[-1]
            if self.h not in pool.by_hash:
                pool.by_hash[self.h], pool.hash_of[b] = b, self.h

    def fork(self):                         # parallel sampling
        s = Seq(self.pool)
        s.table, s.n, s.h, s.cur = list(self.table), self.n, self.h, \
            list(self.cur)
        for b in s.table:
            self.pool.share(b)
        return s

    def free(self):                         # last block evicted first
        for b in reversed(self.table):
            self.pool.drop(b)
        self.table = []
