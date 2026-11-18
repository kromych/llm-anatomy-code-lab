# tool_cost.py -- what the tool of search_notes.py adds to a prompt: the
# tokens of its description, sent with each request, and of one result.
# Usage: python3 tool_cost.py BASE   (llama-server; no embeddings needed)
import sys
import agent, compact

base = sys.argv[1]
messages = [{"role": "system", "content": agent.SYSTEM},
            {"role": "user", "content": "How do I stop a generation?"}]
four = compact.count(messages, base)
import search_notes                      # registers the fifth tool
five = compact.count(messages, base)
print(f"first request: {four} tokens with four tools, {five} with five")

notes = [line.strip() for line in open(search_notes.NOTES)]
call = {"id": "c1", "type": "function", "function": {
    "name": "search_notes", "arguments": '{"query": "stop a generation"}'}}
messages.append({"role": "assistant", "content": None,
                 "tool_calls": [call]})
empty = compact.count(messages + [{"role": "tool", "tool_call_id": "c1",
                                   "content": ""}], base)
sizes = [compact.count(messages + [{"role": "tool", "tool_call_id": "c1",
                                    "content": "\n".join(notes[i:i + 3])}],
                       base) - empty for i in range(0, len(notes), 3)]
print("three notes as a result:", *sizes, "tokens")
