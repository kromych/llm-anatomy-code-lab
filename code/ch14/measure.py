"""measure.py: a model alone versus the same model with MCP tools.

  python3 measure.py QUESTIONS.json BACKEND BASE MODEL OUT.jsonl \
      [--runs N] [--modes alone,tools] -- SERVER COMMAND ...

BACKEND is "openai" (POST BASE/chat/completions, e.g. llama-server or
Ollama's /v1) or "ollama" (Ollama's native POST BASE/api/chat).  Each
question is asked once without tools and once with the tools of the MCP
server; the last line of the reply, "ANSWER: ...", is graded against the
expected answer.  One JSON object per question and mode goes to OUT.jsonl.
"""
import argparse, json, os, re, sys, time, urllib.error, urllib.request
from fractions import Fraction
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "ch13"))
from mcp_client import Connection
from mcp_agent import mcp_tools

MAX_TOKENS = 4096          # per model turn, thinking included
MAX_TURNS = 6

def post(url, body):
    req = urllib.request.Request(url, json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as resp:
        return json.load(resp)

def chat_openai(base, model, messages, tools):
    body = {"model": model, "messages": messages,
            "max_tokens": MAX_TOKENS}
    if tools:
        body["tools"] = tools
    r = post(base + "/chat/completions", body)
    msg = r["choices"][0]["message"]
    calls = [(c["id"], c["function"]["name"],
              json.loads(c["function"]["arguments"] or "{}"))
             for c in msg.get("tool_calls") or []]
    return msg, calls, r.get("usage", {}).get("completion_tokens", 0)

def result_openai(call_id, name, text):
    return {"role": "tool", "tool_call_id": call_id, "content": text}

def chat_ollama(base, model, messages, tools):
    body = {"model": model, "messages": messages, "stream": False,
            "options": {"num_predict": MAX_TOKENS}}
    if tools:
        body["tools"] = tools
    r = post(base + "/api/chat", body)
    msg = r["message"]
    calls = [(c.get("id"), c["function"]["name"],
              c["function"]["arguments"])        # already an object
             for c in msg.get("tool_calls") or []]
    return msg, calls, r.get("eval_count", 0)

def result_ollama(call_id, name, text):
    return {"role": "tool", "tool_name": name, "content": text}

BACKENDS = {"openai": (chat_openai, result_openai),
            "ollama": (chat_ollama, result_ollama)}

def ask(chat, result, base, model, question, conn, tools, server):
    """One question; returns the final text, turns, calls, tokens."""
    messages = [{"role": "user", "content": question}]
    turns = ncalls = tokens = 0
    text = ""
    while turns < MAX_TURNS:
        msg, calls, used = chat(base, model, messages, tools)
        turns, tokens = turns + 1, tokens + used
        text = msg.get("content") or ""
        messages.append(msg)
        if not calls:
            break
        for call_id, called, args in calls:
            ncalls += 1
            name = called.removeprefix(server + "__")
            try:
                r = conn.request("tools/call", {"name": name,
                                                "arguments": args})
                out = "\n".join(c["text"] for c in r["content"]
                                if c["type"] == "text")
            except Exception as e:             # protocol error
                out = "error: %s" % e
            messages.append(result(call_id, called, out))
    return text, turns, ncalls, tokens, messages

def final_answer(text):
    """What follows the last "ANSWER:" (or a box) in the reply."""
    parts = re.split(r"(?i)answer:", text)
    if len(parts) > 1:
        a = parts[-1]
    elif "\\boxed" in text:
        a = text
    else:
        return None
    boxed = re.findall(r"\\boxed\{(.*)\}", a)
    if boxed:
        a = boxed[-1]
    else:
        a = next((l for l in a.splitlines() if l.strip(" *$")), "")
    a = re.sub(r"\\d?frac\{(-?\d+)\}\{(\d+)\}", r"\1/\2", a)
    a = re.sub(r"\\boxed|\\text|\\[ ,;!]|[*`$\\{}]", " ", a)
    a = re.sub(r"(?<=\d)\s+(?=\d)", "", a)      # 3 360 675 -> 3360675
    return " ".join(a.split()).lower() or None

def grade(q, answer):
    if answer is None:
        return False
    e = q["expected"]
    if "matches" in e:                       # an affine-form question
        if not e["matches"]:
            return answer.startswith("no")
        m = re.search(r"x\s*=\s*(-?[\d,]+)", answer)
        return (answer.startswith("yes") and m is not None
                and int(m.group(1).replace(",", "")) == e["x"])
    m = re.match(r"(-?[\d,]+(?:\.\d+)?(?:\s*/\s*[\d,]+)?)", answer)
    if not m:
        return False
    try:
        got = Fraction(m.group(1).replace(",", "").replace(" ", ""))
    except ValueError:
        return False
    return got == Fraction(e["value"])

def main():
    p = argparse.ArgumentParser()
    for a in ("questions", "backend", "base", "model", "out"):
        p.add_argument(a)
    p.add_argument("--runs", type=int, default=1)
    p.add_argument("--modes", default="alone,tools")
    p.add_argument("--server-name", default="tools")
    cut = sys.argv.index("--")
    args, server = p.parse_args(sys.argv[1:cut]), sys.argv[cut + 1:]
    chat, result = BACKENDS[args.backend]
    questions = json.load(open(args.questions))
    conn = Connection(server)
    conn.open()
    tools = mcp_tools(conn, args.server_name)
    with open(args.out, "a") as out:
        for run in range(1, args.runs + 1):
            for q in questions:
                for mode in args.modes.split(","):
                    t = time.perf_counter()
                    try:
                        text, turns, ncalls, tokens, msgs = ask(
                            chat, result, args.base, args.model,
                            q["question"], conn,
                            tools if mode == "tools" else None,
                            args.server_name)
                    except urllib.error.HTTPError as e:   # engine failed
                        err = e.read().decode(errors="replace")
                        text, turns, ncalls, tokens = "", 0, 0, 0
                        msgs = [{"role": "error", "content": err}]
                    secs = time.perf_counter() - t
                    ans = final_answer(text)
                    rec = {"run": run, "id": q["id"], "mode": mode,
                           "backend": args.backend, "model": args.model,
                           "answer": ans, "correct": grade(q, ans),
                           "turns": turns, "tool_calls": ncalls,
                           "tokens": tokens, "seconds": round(secs, 2),
                           "transcript": msgs}
                    out.write(json.dumps(rec) + "\n")
                    out.flush()
                    print("%d %-4s %-5s %-5s %6.1fs %2d turns %s" % (
                        run, q["id"], mode, rec["correct"], secs, turns,
                        ans), file=sys.stderr)
    conn.close()

if __name__ == "__main__":
    main()
