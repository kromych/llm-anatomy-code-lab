# render.py -- render a chat template with Transformers' Jinja settings
#   python3 render.py CONFIG [TEMPLATE.jinja] [MESSAGES.json]
import datetime, json, sys
from jinja2.ext import loopcontrols
from jinja2.sandbox import ImmutableSandboxedEnvironment

def tojson(x, ensure_ascii=False, indent=None, separators=None,
           sort_keys=False):
    return json.dumps(x, ensure_ascii=ensure_ascii, indent=indent,
                      separators=separators, sort_keys=sort_keys)

def raise_exception(message):
    raise ValueError(message)

def strftime_now(fmt):
    return datetime.datetime.now().strftime(fmt)

env = ImmutableSandboxedEnvironment(trim_blocks=True, lstrip_blocks=True,
                                   extensions=[loopcontrols])
env.filters["tojson"] = tojson
env.globals.update(raise_exception=raise_exception,
                   strftime_now=strftime_now)

config = json.load(open(sys.argv[1], encoding="utf-8"))
source = config.get("chat_template")
messages = [{"role": "user", "content": "List the Python files in src/"}]
for path in sys.argv[2:]:        # a template, or messages in a .json file
    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        messages = json.loads(text)
    else:
        source = text
print(env.from_string(source).render(
    messages=messages, add_generation_prompt=True,
    bos_token=config.get("bos_token") or "",
    eos_token=config.get("eos_token") or ""), end="")
