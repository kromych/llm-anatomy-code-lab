"""show_transcript.py: print one recorded conversation of measure.py.

  python3 show_transcript.py RESULTS.jsonl ID MODE [RUN]
Thinking is reduced to its length in characters; lines are wrapped at
72 columns so that the output fits a listing.
"""
import json, sys, textwrap

def show(who, text):
    lines = textwrap.wrap(" ".join(text.split()), 62) or [""]
    print("%-9s %s" % (who, lines[0]))
    for line in lines[1:]:
        print(" " * 10 + line)

def main(path, qid, mode, run=1):
    for line in open(path):
        r = json.loads(line)
        if (r["id"], r["mode"], r["run"]) != (qid, mode, int(run)):
            continue
        print("[%d turns, %d tokens, %.1f s]" % (
            r["turns"], r["tokens"], r["seconds"]))
        for m in r["transcript"]:
            think = m.get("reasoning_content") or m.get("thinking") or ""
            if m["role"] == "user":
                show("user", m["content"])
            elif m["role"] == "tool":
                show("server", m["content"])
            else:
                if think:
                    show("model", "(thinks for %d characters)"
                         % len(think))
                for c in m.get("tool_calls") or []:
                    f = c["function"]
                    args = f["arguments"]
                    if not isinstance(args, str):
                        args = json.dumps(args)
                    show("model", "calls " + f["name"])
                    show("", args)
                if m.get("content"):
                    show("model", m["content"])
        return
    sys.exit("not found")

if __name__ == "__main__":
    main(*sys.argv[1:])
