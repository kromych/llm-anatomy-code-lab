# react.py -- the same loop with a text protocol, for models without tools.
import json, re, urllib.request
import agent
from tools import TOOLS

PROTOCOL = """You can use these tools:
{tools}
To use a tool, reply with exactly two lines and nothing else:
Action: <tool name>
Input: <JSON object with the arguments>
You will receive the result in a line that starts with "Observation:".
When you know the answer, reply with one line: Answer: <the answer>"""

STEP = re.compile(r"Action:\s*(\w+)\s*\nInput:\s*(\{.*?\})\s*$", re.S)

def describe():
    lines = []
    for _, schema in TOOLS.values():
        f = schema["function"]
        args = json.dumps(f["parameters"]["properties"])
        lines.append(f"- {f['name']}: {f['description']} Arguments: {args}")
    return "\n".join(lines)

def complete(messages, base, model):
    body = {"model": model, "messages": messages, "temperature": 0,
            "seed": 1, "stop": ["Observation:"],
            "chat_template_kwargs": {"enable_thinking": False}}
    req = urllib.request.Request(base + "/chat/completions",
                                 json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)

def run(task, base=agent.BASE, model=agent.MODEL, max_turns=12, log=None):
    system = agent.SYSTEM + "\n\n" + PROTOCOL.format(tools=describe())
    messages = [{"role": "system", "content": system},
                {"role": "user", "content": task}]
    for turn in range(max_turns):
        reply = complete(messages, base, model)
        text = reply["choices"][0]["message"]["content"] or ""
        messages.append({"role": "assistant", "content": text})
        if log:
            log(turn, reply)
        if "Answer:" in text:
            return text.split("Answer:", 1)[1].strip(), messages
        m = STEP.search(text)
        if m:
            out = agent.call(m.group(1), m.group(2))
        else:
            out = ("error: reply with Action and Input lines, "
                   "or with Answer:")
        messages.append({"role": "user",
                         "content": "Observation: " + agent.clip(out)})
    return None, messages
