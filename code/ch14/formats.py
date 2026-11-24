"""formats.py: show a tool call and its result as they were sent.

  python3 formats.py RESULTS.jsonl ID [RUN]
Prints, for the first tool call of the recorded conversation, the
assistant message as the engine returned it and the tool message that
measure.py sent back, with reasoning shortened to "...".
"""
import json, sys, textwrap

def show(msg):
    msg = dict(msg)
    for k in ("thinking", "reasoning_content", "reasoning"):
        if msg.get(k):
            msg[k] = "..."
    print("{")
    items = list(msg.items())
    for i, (k, v) in enumerate(items):
        text = "%s: %s%s" % (json.dumps(k), json.dumps(v),
                             "," if i < len(items) - 1 else "")
        for j, line in enumerate(textwrap.wrap(text, 70,
                                               break_long_words=True)):
            print(("  " if j == 0 else "    ") + line)
    print("}")

def main(path, qid, run=1):
    for line in open(path):
        r = json.loads(line)
        if (r["id"], r["mode"], r["run"]) != (qid, "tools", int(run)):
            continue
        msgs = r["transcript"]
        i = next(k for k, m in enumerate(msgs) if m.get("tool_calls"))
        show(msgs[i])
        show(msgs[i + 1])
        return
    sys.exit("not found")

if __name__ == "__main__":
    main(*sys.argv[1:])
