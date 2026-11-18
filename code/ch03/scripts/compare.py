import sys, re
sys.path.insert(0, sys.argv[1])
import bpe
from tokenizers import Tokenizer
QWEN = re.compile(r"(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\nA-Za-z0-9]?[A-Za-z]+"
                  r"|[0-9]| ?[^\sA-Za-z0-9]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+")
tests = ["Hello world", "Tokenization isn't magic: 1234 tokens.",
         "  indented code\n\tfoo(bar, 42);\n", "The quick brown fox jumps over the lazy dog!!",
         "ls src/*.py && echo done", "aaaa bbbb aaaaaaa", "x = [i**2 for i in range(10)]"]
for name, path, pat in (("gpt2", sys.argv[2], bpe.PAT), ("qwen3", sys.argv[3], QWEN)):
    vocab, ranks = bpe.load(path)
    ref = Tokenizer.from_file(path)
    ok = 0
    for t in tests:
        mine = bpe.encode(t, vocab, ranks, pat)
        theirs = ref.encode(t, add_special_tokens=False).ids
        ok += mine == theirs
        if mine != theirs: print(name, "MISMATCH", repr(t), mine, theirs)
    print(name, f"{ok}/{len(tests)} match")
