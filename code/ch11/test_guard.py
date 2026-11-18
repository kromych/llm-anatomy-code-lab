# test_guard.py -- provoke the two failures that guard.py handles, with a
# scripted server whose window holds 1,000 tokens of four characters.
import json, threading
from http.server import ThreadingHTTPServer
import agent, guard, mock

WINDOW = 1000
SCRIPT = [("tool_calls",
           mock.calling("read_file", '{"path": "docs/serving.md"}', 1)),
          ("stop", {"role": "assistant", "content": "Serving"}),
          ("length",                     # cut as llama-server cuts a call
           mock.calling("read_file", '{"path": "docs/formats.md', 2)),
          ("tool_calls",
           mock.calling("read_file", '{"path": "docs/formats.md"}', 2)),
          ("stop", {"role": "assistant", "content": "Model files"})]

class Small(mock.Handler):
    limits = []                          # max_tokens of each chat request
    def do_POST(self):
        n = int(self.headers["Content-Length"])
        body, status = json.loads(self.rfile.read(n)), 200
        if self.path == "/apply-template":
            out = {"prompt": json.dumps(body["messages"])}
        elif self.path == "/tokenize":
            out = {"tokens": [0] * (len(body["content"]) // 4)}
        else:
            Small.limits.append(body["max_tokens"])
            size = len(json.dumps(body["messages"])) // 4
            if size > WINDOW:            # refuse as llama-server does
                status, out = 400, {"error": {
                    "code": 400, "type": "exceed_context_size_error",
                    "n_prompt_tokens": size, "n_ctx": WINDOW}}
            else:
                finish, msg = SCRIPT.pop(0)
                out = {"choices": [{"message": msg,
                                    "finish_reason": finish}]}
        data = json.dumps(out).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 0), Small)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}/v1"
    agent.chat = guard.guarded
    messages = [{"role": "system", "content": agent.SYSTEM}]
    for task in ("What is the title of docs/serving.md?",
                 "And the title of docs/formats.md?"):
        answer, _ = agent.run(task, base, messages=messages)
        print("answer:", answer)
    print("limits sent:", *Small.limits)
    print("oldest tool output:", messages[3]["content"].split(";")[0])
    server.shutdown()
