# agent.py -- prefill work in an agent session, with and without
# prefix caching (uses paged.py).
import random
from paged import Pool, Seq

rng = random.Random(1)
def tokens(n):
    return [rng.randrange(150000) for _ in range(n)]

pool = Pool(n_blocks=8192, block_size=16)
conv = tokens(2000)                     # system prompt and tools
work = total = 0
for turn in range(10):
    seq = Seq(pool)
    hit = seq.prefill(conv)             # steps R4-R6 of Algorithm R
    total += len(conv)
    work += len(conv) - hit
    out = tokens(300)                   # the model's reply (R7)
    for t in out:
        seq.append(t)
    seq.free()
    conv += out + tokens(700)           # reply and tool result (R12)
print(f"prompt tokens {total}, prefilled {work}, "
      f"saved {100 * (total - work) / total:.1f}%")
