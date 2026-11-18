# assemble_r.py -- Algorithm A with the reasoning returned beside the
# message, the answer to an exercise of Chapter 9. The demonstration needs
# no server: its deltas carry the reasoning under both names in use.
import json
from stream import assemble

def assemble_r(chunks):
    """Algorithm A, with the reasoning returned beside the message."""
    chunks, thoughts = list(chunks), ""
    for chunk in chunks:
        for choice in chunk.get("choices", []):
            d = choice.get("delta") or {}
            thoughts += (d.get("reasoning_content")
                         or d.get("reasoning") or "")
    return assemble(chunks) + (thoughts,)

if __name__ == "__main__":
    def delta(d, finish=None):
        return {"choices": [{"index": 0, "delta": d,
                             "finish_reason": finish}]}
    chunks = [delta({"role": "assistant", "reasoning_content": "91 = "}),
              delta({"reasoning": "7 * 13."}),
              delta({"content": "No: 91 is 7 times 13."}, "stop"),
              {"choices": [], "usage": {"prompt_tokens": 21,
                                        "completion_tokens": 14}}]
    msg, finish, usage, thoughts = assemble_r(iter(chunks))
    print(finish, json.dumps(msg))
    print("usage", usage)
    print("reasoning", repr(thoughts))
    assert msg == {"role": "assistant", "content": "No: 91 is 7 times 13."}
    assert thoughts == "91 = 7 * 13."
