# assemble_n.py -- Algorithm A for a stream with several choices (n > 1),
# the answer to an exercise of Chapter 9. The demonstration needs no server:
# its chunks have the shape of the contract, two choices interleaved.
import json
from stream import assemble

def assemble_n(chunks):
    states, usage = {}, None
    for chunk in chunks:
        usage = chunk.get("usage") or usage
        for choice in chunk.get("choices", []):
            st = states.setdefault(choice["index"], [])
            st.append({"choices": [choice]})
    out = [assemble(states[i])[:2] for i in sorted(states)]
    return out, usage

if __name__ == "__main__":
    def delta(i, d, finish=None):
        return {"choices": [{"index": i, "delta": d,
                             "finish_reason": finish}]}
    call = {"index": 0, "id": "call_1", "type": "function",
            "function": {"name": "get_weather", "arguments": '{"ci'}}
    rest = {"index": 0, "function": {"arguments": 'ty": "Oslo"}'}}
    chunks = [delta(0, {"role": "assistant", "content": "Cloudy"}),
              delta(1, {"role": "assistant", "tool_calls": [call]}),
              delta(0, {"content": " in Oslo."}, "stop"),
              delta(1, {"tool_calls": [rest]}, "tool_calls"),
              {"choices": [], "usage": {"prompt_tokens": 20,
                                        "completion_tokens": 30}}]
    out, usage = assemble_n(chunks)
    for msg, finish in out:
        print(finish, json.dumps(msg))
    print("usage", usage)
    assert [f for _, f in out] == ["stop", "tool_calls"]
    args = out[1][0]["tool_calls"][0]["function"]["arguments"]
    assert json.loads(args) == {"city": "Oslo"}
