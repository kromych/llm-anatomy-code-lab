import json, sys
src = open(sys.argv[3]).read().split("config = json.load")[0]
ns = {}; exec(src, ns); env = ns["env"]
config = json.load(open(sys.argv[1], encoding="utf-8"))
source = open(sys.argv[2]).read() if sys.argv[2] != "-" else config["chat_template"]
tools = [{"type": "function", "function": {"name": "bash",
          "description": "Run a shell command",
          "parameters": {"type": "object",
                         "properties": {"command": {"type": "string"}},
                         "required": ["command"]}}}]
call = {"id": "call00001", "type": "function",
        "function": {"name": "bash", "arguments": {"command": "ls src/*.py"}}}
msgs = [{"role": "user", "content": "List the Python files in src/"},
        {"role": "assistant", "content": "", "tool_calls": [call]},
        {"role": "tool", "tool_call_id": "call00001", "name": "bash", "content": "main.py util.py"}]
out = env.from_string(source).render(messages=msgs, tools=tools, add_generation_prompt=True,
                                     bos_token=config.get("bos_token") or "", eos_token=config.get("eos_token") or "")
i = out.find("List the Python files in src/")
print(repr(out[i:]))
