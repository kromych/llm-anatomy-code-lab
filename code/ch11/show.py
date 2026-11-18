# show.py -- stream each turn to the terminal; Ctrl-C cancels the request.
import json, urllib.request
import agent
from stream import sse_events, assemble          # Chapter 9, Algorithm A

def echo(chunks):
    """Print content and tool names as they arrive; pass chunks on."""
    for chunk in chunks:
        for choice in chunk.get("choices", []):
            delta = choice.get("delta", {})
            print(delta.get("content") or "", end="", flush=True)
            for tc in delta.get("tool_calls") or []:
                name = (tc.get("function") or {}).get("name")
                if name:
                    print(f"\n[calling {name}]", flush=True)
        yield chunk

def chat(messages, base=agent.BASE, timeout=300):
    body = {"model": agent.MODEL, "messages": messages,
            "temperature": 0, "seed": 1,
            "tools": [schema for _, schema in agent.TOOLS.values()],
            "chat_template_kwargs": {"enable_thinking": False},
            "stream": True, "stream_options": {"include_usage": True}}
    req = urllib.request.Request(base + "/chat/completions",
                                 json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        chunks = (json.loads(d) for d in sse_events(resp)
                  if d != "[DONE]")
        msg, finish, usage = assemble(echo(chunks))
    return {"choices": [{"message": msg, "finish_reason": finish}],
            "usage": usage}

def converse(tasks, base=agent.BASE):
    """Answer the tasks in one conversation; Ctrl-C cancels a task."""
    agent.chat = chat                            # same loop, streamed turns
    messages = [{"role": "system", "content": agent.SYSTEM}]
    for task in tasks:
        kept = len(messages)
        try:
            agent.run(task.strip(), base, messages=messages)
        except KeyboardInterrupt:      # the connection is closed by now,
            del messages[kept:]        # which cancels the task: forget it
            print("\n[canceled]", end="")
        print()
    return messages

if __name__ == "__main__":
    import sys
    try:
        converse(sys.stdin, *sys.argv[1:2])      # one question per line
    except KeyboardInterrupt:                    # Ctrl-C between questions
        print()
