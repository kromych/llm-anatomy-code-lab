"""mcp_agent.py: a model on an OpenAI-compatible server uses MCP tools.

  python3 mcp_agent.py BASE_URL QUESTION python3 files_server.py ROOT
"""
import json, os, sys, time, urllib.request
from mcp_client import Connection

def chat(base, messages, tools):
    model = os.environ.get("MCP_MODEL", "any")    # Ollama needs a name
    body = json.dumps({"model": model, "messages": messages,
                       "tools": tools}).encode()
    req = urllib.request.Request(base + "/chat/completions", body,
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)["choices"][0]["message"]

def mcp_tools(conn, server):
    """Translate MCP tool definitions into Chat Completions tools."""
    return [{"type": "function", "function": {
                "name": server + "__" + t["name"],   # no dots allowed
                "description": t.get("description", ""),
                "parameters": t["inputSchema"]}}
            for t in conn.request("tools/list")["tools"]]

def run(base, question, argv, server="files", steps=8):
    conn = Connection(argv)
    conn.open()
    tools = mcp_tools(conn, server)
    messages = [{"role": "user", "content": question}]
    for _ in range(steps):
        t = time.perf_counter()
        msg = chat(base, messages, tools)       # POST to the engine
        log("model", t, msg.get("tool_calls") or "final answer")
        messages.append(msg)
        if not msg.get("tool_calls"):
            break
        for call in msg["tool_calls"]:
            name = call["function"]["name"].removeprefix(server + "__")
            args = json.loads(call["function"]["arguments"] or "{}")
            t = time.perf_counter()
            r = conn.request("tools/call", {"name": name,
                                            "arguments": args})
            text = "\n".join(c["text"] for c in r["content"]
                             if c["type"] == "text")
            log("mcp", t, (name, args, text[:60]))
            messages.append({"role": "tool", "tool_call_id": call["id"],
                             "content": text})
    conn.close()
    return msg.get("content")

def log(who, t, what):
    ms = (time.perf_counter() - t) * 1e3
    print("%-5s %7.1f ms  %s" % (who, ms, what), file=sys.stderr)

if __name__ == "__main__":
    print(run(sys.argv[1], sys.argv[2], sys.argv[3:],
              server=os.environ.get("MCP_SERVER", "files")))
