# pytest_tally.py -- sort the failures and errors of a pytest log by the
# exception that ended them: for each block of the sections ERRORS and
# FAILURES, the first line marked "E" that carries an exception.
# usage: python3 pytest_tally.py test_output.txt
import collections, re, sys

EXC = re.compile(r"([A-Za-z_.]*(?:Error|Warning|Exception|Timeout|Failed)"
                 r"[A-Za-z_]*)\b:?\s*(.*)")

text = open(sys.argv[1], encoding="utf-8", errors="replace").read()
start = min(text.index(s) for s in ("= ERRORS =", "= FAILURES =")
            if s in text)
end = text.index("= PASSES =" if "= PASSES =" in text
                 else "short test summary info")
blocks = re.split(r"\n_{3,} (.+?) _{3,}\n", text[start:end])
tally, first = collections.Counter(), {}
for name, block in zip(blocks[1::2], blocks[2::2]):
    marked = [l[1:].strip() for l in block.split("\n")
              if l.startswith("E ")]
    found = next((m for m in map(EXC.match, marked) if m), None)
    if found:
        key = (found.group(1), found.group(2)[:120])
    elif marked and marked[0].startswith("assert"):
        key = ("AssertionError", marked[0][:120])
    else:
        key = ("?", marked[0][:120] if marked else "(no line marked E)")
    kind = "error" if name.startswith("ERROR at") else "failure"
    tally[key + (kind,)] += 1
    first.setdefault(key + (kind,), name)
for (exc, message, kind), n in sorted(tally.items(), key=lambda t: -t[1]):
    print(f"{n:4d} {kind:8s} {exc}: {message}")
    print(f"{'':14s}first: {first[(exc, message, kind)]}")
print(f"{sum(tally.values()):4d} blocks")
