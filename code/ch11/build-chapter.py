# Expand %%LISTING%%, %%EXCERPT%% and %%OUTPUT%% markers from tested files.
import pathlib, re, sys
here = pathlib.Path(__file__).parent
src = pathlib.Path(sys.argv[1]).read_text()

def block(opts, title, text):
    for i, line in enumerate(text.splitlines(), 1):
        assert len(line) <= 76, f"{title}: line {i} has {len(line)} columns"
        assert line.isascii(), f"{title}: line {i} is not ASCII"
    o = f"[{opts}]" if opts else ""
    return f"\\begin{{code}}{o}{{{title}}}\n{text.rstrip()}\n\\end{{code}}"

def expand(m):
    kind, args = m.group(1), m.group(2).split("|")
    if kind == "LISTING":
        f, opts, title = args
        return block(opts, title, (here / f).read_text())
    if kind == "EXCERPT":
        f, start, end, opts, title = args
        lines = (here / f).read_text().splitlines()
        i = next(k for k, l in enumerate(lines) if l.startswith(start))
        j = next(k for k in range(i, len(lines)) if end in lines[k])
        return block(opts, title, "\n".join(lines[i:j + 1]))
    if kind == "OUTPUT":
        f, title = args
        return block("", title, (here / f).read_text())
    raise ValueError(kind)

out = re.sub(r"^%%(LISTING|EXCERPT|OUTPUT) (.*?)%%$", expand, src, flags=re.M)
assert "%%" not in out
pathlib.Path(sys.argv[2]).write_text(out)
