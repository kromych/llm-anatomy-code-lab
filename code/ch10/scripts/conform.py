# conform.py -- check a server against the Chat Completions contract.
# Usage: python3 conform.py BASE_URL MODEL   (standard library only)
import json, sys, urllib.request, urllib.error
import os                   # stream.py is kept with Chapter 9
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "..", "ch09", "scripts"))
from stream import sse_events, assemble

BASE, MODEL = sys.argv[1], sys.argv[2]
NO_THINK = " /no_think" if "qwen3" in MODEL.lower() else ""
WEATHER = {"type": "function", "function": {
    "name": "get_weather", "description": "Current weather in a city",
    "parameters": {"type": "object", "required": ["city"],
                   "properties": {"city": {"type": "string"}}}}}
FINISH = {"stop", "length", "tool_calls", "content_filter"}

def post(body, stream=False):
    body = dict({"model": MODEL, "temperature": 0, "max_tokens": 200},
                **body)
    if "max_completion_tokens" in body:      # the newer name, alone
        del body["max_tokens"]
    req = urllib.request.Request(BASE + "/chat/completions",
            json.dumps(body).encode(),
            {"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=300)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")
    with resp:
        if stream:
            return 200, [d for d in sse_events(resp)]
        return 200, json.load(resp)

def user(text):
    return [{"role": "user", "content": text + NO_THINK}]

def ask_tools(text):        # thinking on: small models decide better
    return [{"role": "system", "content": "Use the tools to answer."},
            {"role": "user", "content": text}]

def whole(r):                 # the reasoning, wherever it is, and the text
    m = r["choices"][0]["message"]
    return (m.get("reasoning_content") or m.get("reasoning") or "") + \
        (m.get("content") or "")

def t_models():
    try:
        with urllib.request.urlopen(BASE + "/models", timeout=60) as resp:
            r = json.load(resp)
    except urllib.error.HTTPError as e:
        raise AssertionError("status %d" % e.code)
    assert r["object"] == "list" and r["data"], r
    assert all(m["object"] == "model" and m["id"] for m in r["data"])

def t_basic():
    code, r = post({"messages": user("Name one planet.")})
    c = r["choices"][0]
    u = r["usage"]
    assert r["object"] == "chat.completion", r.get("object")
    assert c["message"]["role"] == "assistant"
    assert c["finish_reason"] in FINISH, c["finish_reason"]
    assert u["total_tokens"] == u["prompt_tokens"] + u["completion_tokens"]

def t_stream():
    code, events = post({"messages": user("Count to three."),
                         "stream": True,
                         "stream_options": {"include_usage": True}}, True)
    assert events[-1] == "[DONE]", "stream does not end with [DONE]"
    chunks = [json.loads(e) for e in events[:-1]]
    kinds = {c["object"] for c in chunks}
    assert kinds == {"chat.completion.chunk"}, "objects %s" % kinds
    assert chunks[-1]["choices"] == [] and chunks[-1]["usage"], \
        "no final usage chunk with empty choices"
    msg, finish, usage = assemble(chunks)
    assert msg["role"] == "assistant" and finish in FINISH

def t_stop():
    code, r = post({"messages": user("Write the digits 1 to 9, "
                                     "separated by spaces."),
                    "stop": ["5"]})
    c = r["choices"][0]
    assert "5" not in c["message"]["content"]
    assert c["finish_reason"] == "stop"

def t_length():
    code, r = post({"messages": user("Tell a long story."),
                    "max_tokens": 5})
    assert r["choices"][0]["finish_reason"] == "length"

def t_max_completion():
    code, r = post({"messages": user("Tell a long story."),
                    "max_completion_tokens": 5})
    n = r["usage"]["completion_tokens"]
    assert n <= 5, "field ignored: %d tokens" % n
    assert r["choices"][0]["finish_reason"] == "length"

def t_n():
    code, r = post({"messages": user("Say a color."), "n": 2,
                    "temperature": 1})
    assert code == 200, r
    assert [c["index"] for c in r["choices"]] == [0, 1], "n ignored"

def t_logprobs():
    code, r = post({"messages": user("Say yes."), "logprobs": True,
                    "top_logprobs": 3})
    lp = (r["choices"][0].get("logprobs") or {}).get("content")
    assert lp and {"token", "logprob", "top_logprobs"} <= set(lp[0]), lp

def t_seed():
    def draw(seed):
        code, r = post({"messages": user("Write one sentence about "
                                         "the sea."),
                        "temperature": 1, "seed": seed, "max_tokens": 40})
        return whole(r)
    a, b, c = draw(7), draw(7), draw(8)
    assert a == b, "same seed, different text"
    assert a != c, "another seed, the same text"

def t_cached():
    body = {"messages": user("Explain in one line what the prefix cache "
                             "of an inference server is good for."),
            "max_tokens": 5}
    post(body)
    code, r = post(body)                    # the same request again
    details = r["usage"].get("prompt_tokens_details") or {}
    assert details.get("cached_tokens", 0) > 0, "usage %r" % r["usage"]

def t_reasoning():          # thinking on: an extension to the contract
    code, r = post({"messages": [{"role": "user",
                                  "content": "Is 91 a prime number?"}],
                    "max_tokens": 800})
    m = r["choices"][0]["message"]
    assert "<think>" not in (m.get("content") or ""), "tags in content"
    assert not NO_THINK or whole(r) != (m.get("content") or ""), \
        "no reasoning field: %s" % sorted(m)

def call_of(r):
    c = r["choices"][0]
    tc = c["message"].get("tool_calls")
    assert tc, "no tool call: %r" % c["message"].get("content")
    f = tc[0]["function"]
    assert tc[0]["id"] and f["name"] == "get_weather"
    assert isinstance(json.loads(f["arguments"]), dict)
    return c

def t_tool_auto():
    code, r = post({"messages": ask_tools("What is the weather in Oslo?"),
                    "tools": [WEATHER], "max_tokens": 800})
    assert call_of(r)["finish_reason"] == "tool_calls"

def t_tool_required():
    code, r = post({"messages": ask_tools("Hello!"), "tools": [WEATHER],
                    "tool_choice": "required", "max_tokens": 800})
    assert code == 200, r
    call_of(r)

def t_tool_stream():
    code, events = post({"messages": ask_tools("Weather in Lima?"),
                         "tools": [WEATHER], "stream": True,
                         "max_tokens": 800}, True)
    chunks = [json.loads(e) for e in events if e != "[DONE]"]
    msg, finish, usage = assemble(chunks)
    call_of({"choices": [{"message": msg, "finish_reason": finish}]})

def t_schema():
    schema = {"type": "object", "required": ["unit"],
              "additionalProperties": False,
              "properties": {"unit": {"enum": ["celsius", "fahrenheit"]}}}
    code, r = post({"messages": user("Which temperature unit is used "
                                     "in Norway? Answer in JSON."),
                    "response_format": {"type": "json_schema",
                        "json_schema": {"name": "unit", "strict": True,
                                        "schema": schema}}})
    text = r["choices"][0]["message"]["content"]
    try:
        out = json.loads(text)
    except ValueError:
        raise AssertionError("not JSON: %r" % text[:40])
    assert set(out) == {"unit"} and out["unit"] in ("celsius",
                                                     "fahrenheit"), out

def t_error():
    code, r = post({"messages": "not a list"})
    assert 400 <= code < 500, "status %d" % code
    err = r.get("error")
    assert isinstance(err, dict) and "message" in err, "error %r" % err

TESTS = [t_models, t_basic, t_stream, t_stop, t_length,
         t_max_completion, t_n, t_seed, t_logprobs, t_cached,
         t_reasoning, t_tool_auto, t_tool_required, t_tool_stream,
         t_schema, t_error]

for t in TESTS:
    try:
        t()
        print("PASS ", t.__name__)
    except Exception as e:  # report and go on to the next check
        print("FAIL ", t.__name__, "--", type(e).__name__, str(e)[:120])
