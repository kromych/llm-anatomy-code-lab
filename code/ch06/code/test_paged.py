# test_paged.py -- checks of paged.py: sharing, copy on write, prefix
# lookup, and eviction of cached blocks.
from paged import Pool, Seq
p = Pool(8, 4)
a = Seq(p); a.prefill([1,2,3,4,5,6])          # 2 blocks, tail has 2
b = a.fork()                                  # share both blocks
assert p.ref[a.table[0]] == 2 and p.ref[a.table[1]] == 2
b.append(7)                                   # copy on write of tail
assert b.table[0] == a.table[0] and b.table[1] != a.table[1]
assert p.ref[a.table[1]] == 1 and p.ref[b.table[1]] == 1
a.append(9); a.append(10)                     # a's tail fills: cached
c = Seq(p); hit = c.prefill([1,2,3,4,5,6,9,10,11])
assert hit == 8, hit
a.free(); b.free(); c.free()
assert sum(p.ref) == 0 and len(p.free) == 8
# eviction: fill pool with new content, cached blocks get evicted
d = Seq(p); d.prefill(list(range(100, 132)))  # 8 blocks
assert len(p.by_hash) == 8
d.free()
e = Seq(p); hit = e.prefill([1,2,3,4])
assert hit == 0
print("ok", len(p.free))
