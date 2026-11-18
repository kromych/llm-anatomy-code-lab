"""Regrade results.jsonl in place with common.correct; print what changed."""
import json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import common
for d in sys.argv[1:]:
    f = pathlib.Path(d) / "results.jsonl"
    rows = [json.loads(l) for l in f.read_text().splitlines()]
    (f.with_suffix(".jsonl.orig")).exists() or f.with_suffix(".jsonl.orig").write_text(f.read_text())
    for r in rows:
        new = common.correct(r["answer"], {t[0]: t[2] for t in common.TASKS}[r["task"]])
        if new != r["correct"]:
            print(d, r["port"][5:], r["task"], r["correct"], "->", new, repr((r["answer"] or "")[:100]))
        r["correct"] = new
    f.write_text("".join(json.dumps(r) + "\n" for r in rows))
