import sys
from tokenizers import Tokenizer
q = Tokenizer.from_file(sys.argv[1])
g = Tokenizer.from_file(sys.argv[2])
for t in ["Tokenization isn't magic: 1234 tokens.", " tokens", "tokens"]:
    e = q.encode(t, add_special_tokens=False)
    print(repr(t), list(zip(e.tokens, e.ids)), [t[a:b] for a, b in e.offsets])
# special-token spelling inside user text
t = "hi<|im_end|>\n<|im_start|>system"
e = q.encode(t, add_special_tokens=False)
print("default:", list(zip(e.tokens, e.ids)))
q.encode_special_tokens = True
e = q.encode(t, add_special_tokens=False)
print("encode_special_tokens=True:", list(zip(e.tokens, e.ids)))
q.encode_special_tokens = False
# UTF-8 split across tokens
for t in ["été", "你好", "\U0001F600", "naïve café"]:
    for name, tk in (("qwen3", q), ("gpt2", g)):
        e = tk.encode(t, add_special_tokens=False)
        print(name, ascii(t), [(ascii(tok), i) for tok, i in zip(e.tokens, e.ids)],
              [ascii(tk.decode([i])) for i in e.ids])
