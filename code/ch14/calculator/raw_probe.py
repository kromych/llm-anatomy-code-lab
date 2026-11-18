"""raw_probe.py: what does qwen3:1.7b write when Ollama's parser is bypassed?

  python3 raw_probe.py N NAME [NAME ...]
Builds the prompt that Ollama's qwen3 template makes for one tool (the
calculator's, under NAME) and the question below, sends it to
/api/generate with "raw": true, and reports the function name that the
model writes after its reasoning, inside <tool_call> ... </tool_call>.
Ollama's template parser (tools/tools.go) extracts a call only if the
exact tool name occurs in the text after the tag.
"""
import json, os, re, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calc_server import TOOLS

QUESTION = os.environ.get("PROBE_QUESTION",
                          "What is 987654321 * 123456789?")

def prompt(name):
    t = TOOLS[0]
    fn = json.dumps({"name": name, "description": t["description"],
                     "parameters": t["inputSchema"]})
    return ("<|im_start|>system\n\n\n# Tools\n\n"
            "You may call one or more functions to assist with the user "
            "query.\n\nYou are provided with function signatures within "
            "<tools></tools> XML tags:\n<tools>\n"
            '{"type": "function", "function": %s}\n</tools>\n\n'
            "For each function call, return a json object with function "
            "name and arguments within <tool_call></tool_call> XML tags:\n"
            "<tool_call>\n"
            '{"name": <function-name>, "arguments": <args-json-object>}\n'
            "</tool_call><|im_end|>\n"
            "<|im_start|>user\n%s<|im_end|>\n<|im_start|>assistant\n"
            % (fn, QUESTION))

def generate(p):
    body = {"model": "qwen3:1.7b", "raw": True, "prompt": p,
            "stream": False, "options": {"num_predict": 4096}}
    req = urllib.request.Request("http://127.0.0.1:11434/api/generate",
                                 json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.load(r)["response"]

if __name__ == "__main__":
    n, names = int(sys.argv[1]), sys.argv[2:]
    for name in names:
        written = []
        for _ in range(n):
            text = generate(prompt(name))
            after = text.split("</think>", 1)[-1]
            m = re.search(r'<tool_call>\s*\{\s*"name"\s*:\s*"([^"]*)"', after)
            written.append(m.group(1) if m else "(no call)")
            print(name, "->", written[-1], flush=True)
        exact = sum(w == name for w in written)
        print("== %s: exact name in %d of %d; written: %s" % (
            name, exact, n, sorted(set(written))), flush=True)
