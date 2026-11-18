# bpe.py -- byte-level BPE encoder (Algorithm B), standard library only
import json, re, sys

INF = float("inf")

def bytes_to_unicode():
    # GPT-2: printable bytes keep their own code point; the
    # others move to 256, 257, ... so that every byte is visible.
    keep = (list(range(33, 127)) + list(range(161, 173))
            + list(range(174, 256)))
    table, extra = {}, 0
    for b in range(256):
        if b in keep:
            table[b] = chr(b)
        else:
            table[b] = chr(256 + extra)
            extra += 1
    return table

def bpe(word, ranks):
    # merge the adjacent pair of lowest rank until none is left
    parts = list(word)
    while len(parts) > 1:
        rank, i = min((ranks.get(pair, INF), i) for i, pair
                      in enumerate(zip(parts, parts[1:])))
        if rank == INF:
            break
        parts[i:i + 2] = [parts[i] + parts[i + 1]]
    return parts

# GPT-2's pre-tokenizer, restricted to ASCII letters and digits
PAT = re.compile(r"'s|'t|'re|'ve|'m|'ll|'d| ?[A-Za-z]+| ?[0-9]+"
                 r"| ?[^\sA-Za-z0-9]+|\s+(?!\S)|\s+")

def load(path):
    model = json.load(open(path, encoding="utf-8"))["model"]
    merges = [tuple(m.split(" ")) if isinstance(m, str) else tuple(m)
              for m in model["merges"]]
    return model["vocab"], {p: r for r, p in enumerate(merges)}

def encode(text, vocab, ranks, pat=PAT):
    b2u = bytes_to_unicode()
    ids = []
    for chunk in pat.findall(text):
        word = "".join(b2u[b] for b in chunk.encode("utf-8"))
        ids += [vocab[p] for p in bpe(word, ranks)]
    return ids

if __name__ == "__main__":
    vocab, ranks = load(sys.argv[1])
    print(encode(sys.argv[2], vocab, ranks))
