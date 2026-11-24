import json, urllib.request
import common

TOOLS = {f.__name__: f for f in (common.list_files, common.read_file,
                                 common.calculate)}
def schema(fname, description, *params):
    props = {p: {"type": "string"} for p in params}
    return {"type": "function", "function": {
        "name": fname, "description": description,
        "parameters": {"type": "object", "properties": props,
                       "required": list(params)}}}
SCHEMAS = [schema("list_files", "List the files in the workspace."),
           schema("read_file", "Return the contents of one file.", "name"),
           schema("calculate", "Evaluate an arithmetic expression.",
                  "expression")]

def make(base_url):
    def chat(messages):
        body = json.dumps({"model": "local", "messages": messages,
                           "tools": SCHEMAS}).encode()
        req = urllib.request.Request(base_url + "/chat/completions", body,
                                     {"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as r:
            return json.load(r)["choices"][0]["message"]
    def answer(question):
        messages = [{"role": "system", "content": common.SYSTEM},
                    {"role": "user", "content": question}]
        for _ in range(10):
            msg = chat(messages)
            messages.append(msg)
            if not msg.get("tool_calls"):
                return msg.get("content") or ""
            for call in msg["tool_calls"]:
                args = json.loads(call["function"]["arguments"] or "{}")
                out = TOOLS[call["function"]["name"]](**args)
                messages.append({"role": "tool", "content": out,
                                 "tool_call_id": call["id"]})
        return ""
    return answer
