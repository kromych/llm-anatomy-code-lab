# estimate.py -- how far does the usage of one reply predict the next
# prompt? For each request of the session of session.py after the first,
# print the prompt and completion tokens of the reply before it, the
# characters of the message appended since, and the prompt tokens that
# the server then counted.  Usage: python3 estimate.py BASE
import sys
import agent, session

orig, last = agent.chat, {}

def chat(messages, base=agent.BASE, timeout=300):
    reply = orig(messages, base, timeout)
    u = reply["usage"]
    if last:
        new = messages[last["n"] + 1:]           # after the last reply
        chars = sum(len(m["content"]) for m in new)
        known = last["prompt"] + last["completion"]
        more = u["prompt_tokens"] - known
        print(f"{known:5d} tokens + {chars:4d} characters -> "
              f"{u['prompt_tokens']:5d} tokens ({more:3d} more, "
              f"{chars / more:.1f} characters each)")
    last.update(n=len(messages), prompt=u["prompt_tokens"],
                completion=u["completion_tokens"])
    return reply

if __name__ == "__main__":
    agent.chat = chat
    session.session(sys.argv[1], False)
