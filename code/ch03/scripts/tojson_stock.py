# tojson_stock.py -- one tool description through Jinja's own tojson filter
# and through the filter that Transformers installs (as in render.py)
#   python3 tojson_stock.py qwen3/tokenizer_config.json
import json, sys
from jinja2.ext import loopcontrols
from jinja2.sandbox import ImmutableSandboxedEnvironment

def tojson(x, ensure_ascii=False, indent=None, separators=None,
           sort_keys=False):
    return json.dumps(x, ensure_ascii=ensure_ascii, indent=indent,
                      separators=separators, sort_keys=sort_keys)

tools = [{"type": "function", "function": {
    "name": "bash",
    "description": "Run a shell command & return <= 4 KB of output",
    "parameters": {"type": "object",
                   "properties": {"command": {"type": "string"}},
                   "required": ["command"]}}}]
messages = [{"role": "user", "content": "List the Python files in src/"}]
source = json.load(open(sys.argv[1], encoding="utf-8"))["chat_template"]

for label, filters in (("stock", {}), ("transformers", {"tojson": tojson})):
    env = ImmutableSandboxedEnvironment(
        trim_blocks=True, lstrip_blocks=True, extensions=[loopcontrols])
    env.filters.update(filters)
    out = env.from_string(source).render(
        messages=messages, tools=tools, add_generation_prompt=True)
    # Qwen3 writes one line of JSON per tool between <tools> and </tools>
    line = out.split("<tools>\n")[1].split("\n</tools>")[0]
    print(f"{label}: {line}")
