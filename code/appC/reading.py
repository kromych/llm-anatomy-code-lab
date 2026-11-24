r"""reading.py -- the constructs that the listings of this book rely on,
as a session at the prompt of the Python interpreter.  Running the file
repeats every command and compares what it prints with the lines below.

Usage: python3 reading.py [-v]

Values and containers:

>>> ids = [504, 3575, 282, 4649, 314]         # a list of token IDs
>>> ids[0], ids[-1], ids[1:3], ids[:2]        # indexes and slices
(504, 314, [3575, 282], [504, 3575])
>>> meta = {"magic": "GGUF", "version": 3}    # a dictionary
>>> meta["version"], meta.get("tensors"), meta.get("tensors", 0)
(3, None, 0)
>>> name, size = "gemma.gguf", 806058240      # a tuple, unpacked
>>> f"{name}: {size / 1e6:.0f} MB or {size:,} bytes"
'gemma.gguf: 806 MB or 806,058,240 bytes'
>>> "large" if size > 1e9 else "small"        # a conditional expression
'small'

Loops written as expressions:

>>> [t for t in ids if t > 500]               # a list comprehension
[504, 3575, 4649]
>>> {t: i for i, t in enumerate(ids)}[282]    # a dictionary of positions
2
>>> sum(x * y for x, y in zip([1, 2, 0], [1, 2, 0]))    # a dot product
5
>>> sorted(ids, key=lambda t: t % 100)[:3]    # by their last two digits
[504, 314, 4649]

Bytes and bits:

>>> head = "GGUF".encode() + bytes([3, 0, 0, 0])
>>> head, head[:4].decode(), head.hex()
(b'GGUF\x03\x00\x00\x00', 'GGUF', '4747554603000000')
>>> import struct
>>> struct.unpack("<4sI", head), struct.unpack(">4sI", head)
((b'GGUF', 3), (b'GGUF', 50331648))
>>> 1 << 15, 0x9f, 0x9f >> 4, 0x9f & 0x0f     # shifts and masks
(32768, 159, 9, 15)

A decorator, a class, and an exception:

>>> TOOLS = {}
>>> def tool(f):                    # a decorator: a function that takes
...     TOOLS[f.__name__] = f       # the function defined below it
...     return f
>>> @tool
... def add(a: int, b: int = 1) -> int:
...     return a + b
>>> add(2), TOOLS["add"](2, 3), add.__annotations__["b"]
(3, 5, <class 'int'>)
>>> class Budget:                   # a class: data with its functions
...     def __init__(self, limit):
...         self.limit, self.used = limit, 0
...     def spend(self, n):
...         if self.used + n > self.limit:
...             raise ValueError(f"{n} tokens exceed the budget")
...         self.used += n
>>> budget = Budget(100)
>>> budget.spend(60)
>>> try:
...     budget.spend(50)
... except ValueError as e:
...     print("refused:", e)
refused: 50 tokens exceed the budget
>>> budget.used, isinstance(budget, Budget)
(60, True)
"""
import doctest

if __name__ == "__main__":
    print(doctest.testmod())
