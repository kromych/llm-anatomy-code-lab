"""Input filter for Algorithm D (Exercise 12.8).

Passes the user's messages and the assistant's final answers to the next
agent, dropping assistant tool-call turns and their tool results together.
"""


def handoff_filter(history):
    return [m for m in history
            if m["role"] == "user"
            or (m["role"] == "assistant" and not m.get("tool_calls"))]


if __name__ == "__main__":
    sample = [
        {"role": "system", "content": "You triage requests."},
        {"role": "user", "content": "Check invoice 42."},
        {"role": "assistant", "content": None,
         "tool_calls": [{"id": "c0", "type": "function",
                         "function": {"name": "transfer_to_billing",
                                      "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "c0",
         "content": '{"assistant": "billing"}'},
    ]
    assert handoff_filter(sample) == [
        {"role": "user", "content": "Check invoice 42."}]
