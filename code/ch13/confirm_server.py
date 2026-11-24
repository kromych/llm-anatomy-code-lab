"""confirm_server.py: files_server.py with a request for input.

  python3 confirm_server.py ROOT

read_file asks the user, through the client, before it returns a text of
more than LIMIT characters.  The question travels in a result of type
input_required, and the answer returns in a second tools/call.
"""
import base64, hashlib, hmac, json, os
import files_server as fs

LIMIT = 1000
KEY = os.urandom(32)       # replicas of an HTTP server would share it
CAPS = fs.P + "clientCapabilities"

def seal(state):
    """Encode the state and sign it: it returns through the client."""
    body = base64.urlsafe_b64encode(json.dumps(state).encode()).decode()
    return body + "." + hmac.new(KEY, body.encode(),
                                 hashlib.sha256).hexdigest()

def unseal(text):
    body, _, mac = str(text).partition(".")
    good = hmac.new(KEY, body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(mac.encode(), good.encode()):
        raise fs.RpcError(-32602, "Invalid requestState")
    return json.loads(base64.urlsafe_b64decode(body))

def question(state):
    return {"method": "elicitation/create", "params": {
        "mode": "form",
        "message": "%(path)s has %(size)d characters." % state,
        "requestedSchema": {"type": "object", "required": ["whole"],
            "properties": {"whole": {"type": "boolean",
                "title": "Return the whole file?"}}}}}

answer_one = fs.handle     # Algorithm O, unchanged

def handle(msg):
    result = answer_one(msg)
    params = msg.get("params") or {}
    if (result is None or fs.legacy or msg.get("method") != "tools/call"
            or params.get("name") != "read_file" or result["isError"]):
        return result                  # everything else is unchanged
    text = result["content"][0]["text"]
    if len(text) <= LIMIT:
        return result
    state = {"path": params["arguments"]["path"], "size": len(text)}
    reply = (params.get("inputResponses") or {}).get("confirm")
    if reply and unseal(params.get("requestState")) == state:
        if reply.get("action") != "accept":
            text, result["isError"] = "the user declined", True
        elif not (reply.get("content") or {}).get("whole"):
            text = text[:LIMIT]
        result["content"][0]["text"] = text
        return result
    if "elicitation" not in params["_meta"][CAPS]:
        raise fs.RpcError(-32021, "read_file needs elicitation",
                          {"requiredCapabilities": {"elicitation": {}}})
    return {"resultType": "input_required",
            "inputRequests": {"confirm": question(state)},
            "requestState": seal(state), "_meta": result["_meta"]}

if __name__ == "__main__":
    fs.handle = handle
    fs.main()
