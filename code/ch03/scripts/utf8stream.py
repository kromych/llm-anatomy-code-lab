# utf8stream.py -- emit decoded text in whole UTF-8 characters (Algorithm U)
#   python3 utf8stream.py gpt2/tokenizer.json 140 253 21169 18849 38857 \
#     16843 20375
import json, sys

def split_complete(buf):
    # return (ready, pending): pending is an unfinished character
    for k in range(1, min(4, len(buf)) + 1):
        b = buf[-k]
        if b & 0xC0 == 0x80:           # continuation byte: look further
            continue
        n = 1 if b < 0x80 else 2 if b < 0xE0 else 3 if b < 0xF0 else 4
        if n > k:                      # lead byte whose tail is missing
            return buf[:-k], buf[-k:]
        break
    return buf, b""

def stream(pieces):
    pending = b""
    for piece in pieces:               # the bytes of each new token
        ready, pending = split_complete(pending + piece)
        if ready:
            yield ready.decode("utf-8", errors="replace")
    if pending:                        # end of stream: flush the rest
        yield pending.decode("utf-8", errors="replace")

if __name__ == "__main__":
    from bpe import bytes_to_unicode
    vocab = json.load(open(sys.argv[1], encoding="utf-8"))["model"]["vocab"]
    inv = {i: t for t, i in vocab.items()}
    u2b = {u: b for b, u in bytes_to_unicode().items()}
    ids = [int(x) for x in sys.argv[2:]]
    pieces = [bytes(u2b[c] for c in inv[i]) for i in ids]
    print([p.hex(" ") for p in pieces])
    print([ascii(s) for s in stream(pieces)])
