# endpoints.py -- one request to each endpoint that a server may offer
# beside /v1/chat/completions; prints the status and the shape of each
# answer.  Usage: python3 endpoints.py ROOT_URL MODEL
# (standard library only; ROOT_URL without /v1)
import json, sys, urllib.request, urllib.error

ROOT, MODEL = sys.argv[1], sys.argv[2]
HI = [{"role": "user", "content": "Say hi."}]
PROBES = [
    ("GET", "/v1/models", None),
    ("POST", "/v1/completions", {"prompt": "One, two, three,",
                                 "max_tokens": 4}),
    ("POST", "/v1/embeddings", {"input": "Hello, seam!"}),
    ("POST", "/v1/responses", {"input": "Say hi.",
                               "max_output_tokens": 8}),
    ("POST", "/v1/messages", {"messages": HI, "max_tokens": 8}),
    ("POST", "/v1/rerank", {"query": "seam", "documents": ["a", "b"]}),
    ("GET", "/health", None),
    ("GET", "/metrics", None),
    ("GET", "/props", None),
    ("GET", "/slots", None),
    ("POST", "/tokenize", {"content": "Hello, seam!"}),
    ("POST", "/detokenize", {}),
    ("POST", "/apply-template", {"messages": HI}),
    ("GET", "/", None),
    ("GET", "/api/version", None),
    ("GET", "/api/tags", None),
    ("POST", "/api/embed", {"input": "Hello, seam!"}),
]

SHOW = ("object", "status", "type", "version")

def shape(x):
    """A short description of a JSON value: its keys, not its contents."""
    if isinstance(x, dict):
        return "{" + ", ".join(
            "%s=%s" % (k, v) if k in SHOW and isinstance(v, str) else k
            for k, v in x.items()) + "}"
    if isinstance(x, list):
        return "[%d] %s" % (len(x), shape(x[0]) if x else "")
    return type(x).__name__

tokens = [9707, 11, 26396, 0]        # "Hello, seam!" for Qwen3

for method, path, body in PROBES:
    data = None
    if path == "/detokenize":
        body = {"tokens": tokens}
    if body is not None:
        data = json.dumps(dict({"model": MODEL}, **body)).encode()
    req = urllib.request.Request(ROOT + path, data,
            {"Content-Type": "application/json"}, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=300)
    except urllib.error.HTTPError as e:
        resp = e
    text = resp.read().decode("utf-8", "replace")
    try:
        reply = json.loads(text)
        text = shape(reply)
        if path == "/tokenize" and resp.status == 200:
            tokens = reply["tokens"]
        if path == "/v1/models" and resp.status == 200:
            text += " ids %s" % [m["id"] for m in reply["data"]]
            meta = reply["data"][0].get("meta")
            if meta:                    # llama-server: sizes of the model
                text += " meta %s" % json.dumps(meta)
    except ValueError:
        text = repr(text.strip()[:40])
    print("%-4s %-16s %d %s" % (method, path, resp.status, text))

def call(path, body):
    req = urllib.request.Request(ROOT + path, json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.load(resp)
    except urllib.error.HTTPError:
        return {}

# Where a server renders templates and tokenizes: the prompt of one
# message, its tokens, and what the chat endpoint counts for it.
prompt = call("/apply-template", {"messages": HI}).get("prompt")
if prompt:
    n = len(call("/tokenize", {"content": prompt})["tokens"])
    chat = call("/v1/chat/completions", {"model": MODEL, "messages": HI,
                                         "max_tokens": 1})
    print("prompt %r: %d tokens; the chat endpoint counts %d" % (
        prompt, n, chat["usage"]["prompt_tokens"]))
