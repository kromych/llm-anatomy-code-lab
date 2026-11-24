"""search_run.py: our agent with an MCP server, recording the conversation.

  python3 search_run.py BASE MODEL QUESTION OUT.jsonl -- SERVER COMMAND ...
The loop is that of ../../ch13/mcp_agent.py (prefix "web").  One JSON
object, with the messages, the tool calls and their times, is appended to
OUT.jsonl, and the conversation is printed in the form of the book's
listings.
"""
import json, os, sys, textwrap, time, urllib.request
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..",
                                "ch13"))
from mcp_client import Connection
from mcp_agent import mcp_tools

MAX_TOKENS = 4096          # per model turn, thinking included
MAX_TURNS = 8

def chat(base, model, messages, tools):
    body = {"model": model, "messages": messages, "tools": tools,
            "max_tokens": MAX_TOKENS}
    req = urllib.request.Request(base + "/chat/completions",
                                 json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as resp:
        r = json.load(resp)
    return r["choices"][0]["message"], r.get("usage", {})

def run(base, model, question, argv, server="web"):
    conn = Connection(argv)
    conn.open()
    tools = mcp_tools(conn, server)
    messages = [{"role": "user", "content": question}]
    steps, t0 = [], time.time()
    for _ in range(MAX_TURNS):
        t = time.perf_counter()
        msg, usage = chat(base, model, messages, tools)
        steps.append({"who": "model", "ms": (time.perf_counter() - t) * 1e3,
                      "usage": usage})
        messages.append(msg)
        if not msg.get("tool_calls"):
            break
        for call in msg["tool_calls"]:
            name = call["function"]["name"].removeprefix(server + "__")
            args = json.loads(call["function"]["arguments"] or "{}")
            t = time.perf_counter()
            r = conn.request("tools/call", {"name": name,
                                            "arguments": args}, timeout=60)
            text = "\n".join(c["text"] for c in r["content"]
                             if c["type"] == "text")
            steps.append({"who": "mcp", "tool": name, "args": args,
                          "ms": (time.perf_counter() - t) * 1e3,
                          "error": r.get("isError", False),
                          "chars": len(text)})
            messages.append({"role": "tool", "tool_call_id": call["id"],
                             "content": text})
    conn.close()
    return {"question": question, "model": model, "base": base,
            "date": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(t0)),
            "seconds": time.time() - t0, "steps": steps,
            "transcript": messages}

def show(who, text, width=62):
    lines = textwrap.wrap(" ".join(text.split()), width,
                          break_on_hyphens=False) or [""]
    print("%-9s %s" % (who, lines[0]))
    for line in lines[1:]:
        print(" " * 10 + line)

def print_run(r, keep=3):
    print("[%s, %d model turns, %.1f s]" % (
        r["date"], sum(s["who"] == "model" for s in r["steps"]),
        r["seconds"]))
    for m in r["transcript"]:
        think = m.get("reasoning_content") or m.get("reasoning") or ""
        if m["role"] == "user":
            show("user", m["content"])
        elif m["role"] == "tool":
            lines = m["content"].splitlines()
            for i, line in enumerate(lines[:keep]):
                show("server" if i == 0 else "", line)
            if len(lines) > keep:
                show("", "[... %d more lines, %d characters in all]"
                     % (len(lines) - keep, len(m["content"])))
        else:
            if think:
                show("model", "(thinks for %d characters)" % len(think))
            for c in m.get("tool_calls") or []:
                show("model", "calls " + c["function"]["name"])
                show("", c["function"]["arguments"])
            if m.get("content"):
                show("model", m["content"])

if __name__ == "__main__":
    base, model, question, out = sys.argv[1:5]
    argv = sys.argv[sys.argv.index("--") + 1:]
    r = run(base, model, question, argv)
    with open(out, "a") as f:
        f.write(json.dumps(r) + "\n")
    print_run(r)
