# test_parallel.py -- two tool calls in one reply, one of them failing.
import agent, mock

def call(i, path):
    return {"id": f"call_{i}", "type": "function", "function": {
        "name": "read_file", "arguments": f'{{"path": "{path}"}}'}}

mock.SCRIPT[:] = [{"role": "assistant", "content": None,
                   "tool_calls": [call("a", "README.md"),
                                  call("b", "missing.txt")]},
                  {"role": "assistant", "content": "done"}]
server, base = mock.serve()
answer, _ = agent.run("Read README.md and missing.txt.", base)
for m in mock.Handler.received[1]:
    text = (m["content"] or "").replace("\n", " ")
    print(m["role"], m.get("tool_call_id", "-"), text[:40])
server.shutdown()
