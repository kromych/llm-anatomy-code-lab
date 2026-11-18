# visitor.py ROOT_URL KIND -- what a visitor without a key can learn from
# a model server and change in it. KIND is llama (llama-server with one
# model), router (llama-server without a model), or ollama. The probes
# that would change something name a model that does not exist, so the
# status tells whether the door is open and nothing is lost.
# Standard library only.
import json, sys, urllib.request, urllib.error

ROOT, KIND = sys.argv[1], sys.argv[2]
GHOST = "no-such-model-here"
PAGE = {"Origin": "http://example.com"}  # as a browser adds for a page

def ask(method, path, body=None, headers={}):
    data = json.dumps(body).encode() if body is not None else None
    head = dict({"Content-Type": "application/json"}, **headers)
    req = urllib.request.Request(ROOT + path, data, head, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=60)
    except urllib.error.HTTPError as e:
        resp = e
    text = resp.read().decode(errors="replace")
    return resp.status, text, resp.headers

def show(method, path, body=None, note=lambda text: ""):
    status, text, _ = ask(method, path, body)
    _, _, headers = ask("OPTIONS", path, None, dict(
        PAGE, **{"Access-Control-Request-Method": method}))
    page = headers.get("Access-Control-Allow-Origin") or "-"
    page = "any page" if page == PAGE["Origin"] else "no page"
    print(f"{method:6} {path:21} {status}  {page:8}  {note(text)}")

def said(text):                          # the error, or the keys
    try:
        reply = json.loads(text)
    except ValueError:
        return ""
    error = reply.get("error")
    if isinstance(error, dict):
        error = error.get("message")
    return (error or "keys: " + " ".join(sorted(reply)))[:27]

def has(*words):
    return lambda text: ("holds: " + " ".join(
        w for w in words if w in text)) if words[0] in text else said(text)

def listed(key):
    return lambda text: ("%d models listed" % len(json.loads(text)[key])
                         if key in text else said(text))

print("method path                 status, from a page?, and the reply")
if KIND == "llama":
    ask("POST", "/v1/chat/completions", {"max_tokens": 8, "messages": [
        {"role": "user", "content": "My password is hunter2."}]})
    show("GET", "/props", note=has("model_path", "chat_template"))
    show("GET", "/slots", note=has("n_ctx", "is_processing", "hunter2"))
    show("POST", "/props", {"x": 1}, said)
    show("POST", "/slots/0?action=save", {"filename": "x.bin"}, said)
    show("GET", "/metrics", note=said)
elif KIND == "router":
    show("GET", "/models", note=listed("data"))
    show("POST", "/models/load", {"model": GHOST}, said)
    show("POST", "/models/unload", {"model": GHOST}, said)
    show("DELETE", "/models", {"model": GHOST}, said)
else:
    show("GET", "/api/tags", note=listed("models"))
    show("GET", "/api/ps", note=said)
    show("POST", "/api/show", {"model": GHOST}, said)
    show("DELETE", "/api/delete", {"model": GHOST}, said)
