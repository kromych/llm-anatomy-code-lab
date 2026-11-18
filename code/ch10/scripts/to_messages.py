# to_messages.py -- a conversation of the Chat Completions API in the form
# of Anthropic's Messages API, the answer to an exercise of Chapter 10. The
# demonstration needs no server.
import json

def to_messages(chat):
    system, out = [], []
    for m in chat:
        if m["role"] in ("system", "developer"):
            system.append(m["content"])
        elif m["role"] == "tool":
            block = {"type": "tool_result",
                     "tool_use_id": m["tool_call_id"],
                     "content": m["content"]}
            if out and out[-1]["role"] == "user" and \
                    isinstance(out[-1]["content"], list):
                out[-1]["content"].append(block)
            else:
                out.append({"role": "user", "content": [block]})
        elif m["role"] == "assistant":
            blocks = []
            if m.get("content"):
                blocks.append({"type": "text", "text": m["content"]})
            for c in m.get("tool_calls") or []:
                blocks.append({"type": "tool_use", "id": c["id"],
                               "name": c["function"]["name"],
                               "input": json.loads(
                                   c["function"]["arguments"])})
            out.append({"role": "assistant", "content": blocks})
        else:
            out.append({"role": "user", "content": m["content"]})
    return "\n\n".join(system), out

if __name__ == "__main__":
    def call(i, city):
        return {"id": i, "type": "function", "function": {
            "name": "get_weather",
            "arguments": json.dumps({"city": city})}}
    chat = [{"role": "system", "content": "Use the tools to answer."},
            {"role": "user", "content": "Weather in Oslo and Lima?"},
            {"role": "assistant", "content": "I will look.",
             "tool_calls": [call("c1", "Oslo"), call("c2", "Lima")]},
            {"role": "tool", "tool_call_id": "c1", "content": "cloudy"},
            {"role": "tool", "tool_call_id": "c2", "content": "sunny"},
            {"role": "assistant", "content": "Cloudy and sunny."}]
    system, messages = to_messages(chat)
    print("system:", system)
    for m in messages:
        print(json.dumps(m))
    assert [m["role"] for m in messages] == ["user", "assistant", "user",
                                             "assistant"]
    kinds = [b["type"] for b in messages[2]["content"]]
    assert kinds == ["tool_result", "tool_result"]
    assert messages[1]["content"][1]["input"] == {"city": "Oslo"}
