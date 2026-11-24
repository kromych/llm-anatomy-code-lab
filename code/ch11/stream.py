import json, sys, urllib.request

def sse_events(resp):
    """Yield the data of each server-sent event (one or more data lines)."""
    data = []
    for raw in resp:
        line = raw.decode("utf-8").rstrip("\r\n")
        if line == "":                       # a blank line ends an event
            if data:
                yield "\n".join(data)
            data = []
        elif line.startswith("data:"):
            data.append(line[5:].removeprefix(" "))
        # lines starting with ":" are comments; other fields are ignored

def assemble(chunks):
    """Algorithm A: build the final message from streamed deltas."""
    msg = {"role": None, "content": ""}
    calls, finish, usage = {}, None, None
    for chunk in chunks:                                     # A1
        usage = chunk.get("usage") or usage                  # A2
        for choice in chunk.get("choices", []):
            delta = choice.get("delta", {})
            msg["role"] = delta.get("role") or msg["role"]   # A3
            msg["content"] += delta.get("content") or ""
            for tc in delta.get("tool_calls") or []:         # A4
                c = calls.setdefault(tc["index"], {"id": None,
                        "type": "function",
                        "function": {"name": "", "arguments": ""}})
                c["id"] = tc.get("id") or c["id"]
                f = tc.get("function") or {}
                c["function"]["name"] += f.get("name") or ""
                c["function"]["arguments"] += f.get("arguments") or ""
            finish = choice.get("finish_reason") or finish   # A5
    if calls:                                                # A6
        msg["tool_calls"] = [calls[i] for i in sorted(calls)]
    return msg, finish, usage

def stream_chat(url, body):
    body = dict(body, stream=True,
                stream_options={"include_usage": True})
    req = urllib.request.Request(url, json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        chunks = (json.loads(d) for d in sse_events(resp)
                  if d != "[DONE]")
        return assemble(chunks)

if __name__ == "__main__":
    url = sys.argv[1] + "/chat/completions"
    msg, finish, usage = stream_chat(url, {"model": sys.argv[2],
        "messages": [{"role": "user", "content": sys.argv[3]}]})
    print(json.dumps(msg, indent=1), finish, usage, sep="\n")
