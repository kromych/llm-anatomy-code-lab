"""confirm_client.py: a client that answers requests for input.

  python3 confirm_client.py PATH python3 confirm_server.py ROOT

Calls read_file for PATH.  When the server asks for input, the program
puts the question on the terminal and repeats the call with the answer.
"""
import sys
from mcp_client import Connection

def ask(p):
    """Answer one elicitation/create in form mode on the terminal."""
    print(p["message"], file=sys.stderr)
    content = {}
    for key, prop in p["requestedSchema"]["properties"].items():
        if prop.get("type") != "boolean":
            return {"action": "cancel"}       # we know yes and no only
        reply = input(prop.get("title", key) + " [y/n/q] ").strip()
        if reply not in ("y", "n"):
            return {"action": "decline"}
        content[key] = reply == "y"
    return {"action": "accept", "content": content}

class Asking(Connection):
    def __init__(self, argv):
        super().__init__(argv)
        self.caps = {"elicitation": {"form": {}}}

    def request(self, method, params=None, timeout=30):
        """Repeat the request with the answers while the server asks."""
        r = super().request(method, params, timeout)
        while r.get("resultType") == "input_required":
            again = dict(params or {}, inputResponses={
                key: ask(req["params"])
                for key, req in r.get("inputRequests", {}).items()})
            if "requestState" in r:           # goes back as it came
                again["requestState"] = r["requestState"]
            r = super().request(method, again, timeout)
        return r

if __name__ == "__main__":
    c = Asking(sys.argv[2:])
    c.open()
    r = c.request("tools/call", {"name": "read_file",
                                 "arguments": {"path": sys.argv[1]}})
    text = r["content"][0]["text"]
    print("isError %s, %d characters" % (r["isError"], len(text)))
    print(text[:150])
    c.close()
