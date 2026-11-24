"""A model that never learns, for testing a harness's guard against
repeated tool calls: every request that offers tools is answered with the
same call, at most N times, and then with the word "done". It speaks
Chat Completions and, for Codex, the Responses API. Each request is
reported on standard output with the last message that the harness sent,
which shows what the model would have been told.

usage: python3 repeat_server.py PORT TOOL ARGUMENTS_JSON [N]"""
import json, sys, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT, TOOL, ARGS = int(sys.argv[1]), sys.argv[2], sys.argv[3]
LIMIT = int(sys.argv[4]) if len(sys.argv) > 4 else 20
json.loads(ARGS)                         # the arguments must be JSON
lock, state = threading.Lock(), {"requests": 0, "calls": 0}

def text_of(content):
    if isinstance(content, list):
        return " ".join(str(p.get("text", p)) for p in content)
    return str(content)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.reply({"object": "list",
                    "data": [{"id": "repeat", "object": "model"}]})

    def do_POST(self):
        q = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        tools = [t.get("function", t).get("name")
                 for t in q.get("tools", [])]
        if "input" in q:
            return self.items(q, tools)
        last = q["messages"][-1]
        with lock:
            state["requests"] += 1
            n = state["requests"]
            call = bool(tools) and state["calls"] < LIMIT
            state["calls"] += call
            k = state["calls"]
        print("request %d: %d tools, last message %s: %s" % (
            n, len(tools), last["role"],
            text_of(last.get("content"))[:300].replace("\n", " ")),
            flush=True)
        if n == 1 or (tools and k == 1 and call):
            print("  tools offered:", " ".join(tools), flush=True)
        if call:
            print("  -> call %d of %s" % (k, TOOL), flush=True)
            delta = {"role": "assistant", "content": None, "tool_calls": [{
                "index": 0, "id": "call_%d" % k, "type": "function",
                "function": {"name": TOOL, "arguments": ARGS}}]}
            finish = "tool_calls"
        else:
            delta = {"role": "assistant",
                     "content": "done" if tools else "A title"}
            finish = "stop"
        usage = {"prompt_tokens": 1, "completion_tokens": 1,
                 "total_tokens": 2}
        base = {"id": "chatcmpl-%d" % n, "created": 0, "model": "repeat"}
        if not q.get("stream"):
            return self.reply(dict(base, object="chat.completion",
                usage=usage, choices=[{"index": 0, "message": delta,
                                       "finish_reason": finish}]))
        chunk = dict(base, object="chat.completion.chunk")
        events = [dict(chunk, choices=[{"index": 0, "delta": delta,
                                        "finish_reason": None}]),
                  dict(chunk, choices=[{"index": 0, "delta": {},
                                        "finish_reason": finish}]),
                  dict(chunk, choices=[], usage=usage)]
        body = "".join("data: %s\n\n" % json.dumps(e) for e in events)
        self.send(body + "data: [DONE]\n\n", "text/event-stream")

    def items(self, q, tools):       # the Responses API
        items = q["input"] if isinstance(q["input"], list) else []
        last = items[-1] if items else {}
        with lock:
            state["requests"] += 1
            n = state["requests"]
            call = state["calls"] < LIMIT
            state["calls"] += call
            k = state["calls"]
        print("request %d: %d tools, last item %s: %s" % (
            n, len(tools), last.get("type", last.get("role")),
            text_of(last.get("output", last.get("content")))[:300]
            .replace("\n", " ")), flush=True)
        if call:
            print("  -> call %d of %s" % (k, TOOL), flush=True)
            item = {"type": "function_call", "id": "fc_%d" % k,
                    "call_id": "call_%d" % k, "name": TOOL,
                    "arguments": ARGS, "status": "completed"}
        else:
            item = {"type": "message", "id": "msg_%d" % n,
                    "role": "assistant", "status": "completed",
                    "content": [{"type": "output_text", "text": "done",
                                 "annotations": []}]}
        response = {"id": "resp_%d" % n, "object": "response",
                    "model": "repeat", "output": [],
                    "usage": {"input_tokens": 1, "output_tokens": 1,
                              "total_tokens": 2}}
        events = [
            {"type": "response.created",
             "response": dict(response, status="in_progress")},
            {"type": "response.output_item.done", "output_index": 0,
             "item": item},
            {"type": "response.completed",
             "response": dict(response, status="completed",
                              output=[item])}]
        self.send("".join("event: %s\ndata: %s\n\n" % (
            e["type"], json.dumps(e)) for e in events),
            "text/event-stream")

    def reply(self, obj):
        self.send(json.dumps(obj), "application/json")

    def send(self, body, kind):
        data = body.encode()
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass

ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
