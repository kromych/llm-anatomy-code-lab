# A calculator over MCP (Chapter 14, "Tools for exact arithmetic")

- `calc_server.py` - stdio MCP server (standard library only) with one
  tool, `calculate(expression)`. The expression is parsed with `ast` and
  evaluated by walking the tree: numbers, + - * / // % **, unary signs
  and parentheses only; exact integers and `fractions.Fraction`; at most
  500 characters and 10,000 bits per number; powers checked before they
  are computed. `eval` and `exec` are never used.
- `make_questions.py` - writes `questions.json`: 12 arithmetic questions
  (long products, nested parentheses, large powers, fractions).
- `results/ollama-native.jsonl` - `../measure.py` with Ollama's native
  /api/chat, tool prefix `calculator__`, with and without the tool,
  2 runs; `results/ollama-native-calc.jsonl` - the same with the prefix
  `calc__`, tool only; `results/ollama-v1-tools.jsonl` - Ollama's
  OpenAI-compatible /v1, prefix `calculator__`, tool only;
  `results/llama-server-tools.jsonl` - llama-server, prefix
  `calculator__`, tool only.
- `results/ollama-empty-probe.txt` - with the prefix `calculator__`,
  Ollama often returned neither text nor a tool call; this probe varies
  only the tool's name (8 requests each): a call in 1 of 8 requests for
  `calculator__calculate` and in 8 of 8 for each of `calculate`,
  `calc_calculate`, `calc__calculate` and `math__calculate`. Cause not
  found.
- `empty_probe.py` - repeats the probe through `/api/chat` and checks
  whether an empty reply hides a call in its thinking:
  `results/empty_probe-thinking.txt` (question c02) and
  `results/empty_probe-thinking-short.txt` (the probe's original question;
  3 of 8 calls for `calculator__calculate`, 8 of 8 for `calc__calculate`;
  no call in any thinking).
- `raw_probe.py` - the same question in raw mode (`/api/generate`,
  prompt built from the qwen3 template): the model writes the exact name
  in 8 of 8 attempts for both names (`results/raw_probe-names.txt`), so
  the call is lost inside Ollama. The parser that Ollama uses for
  templates without a parser of their own (tools/tools.go in v0.40.16)
  keeps everything after `<tool_call>` until it can extract a call, and
  returns none of that text when it cannot, so a call that it fails to
  recognize leaves no trace in the reply.
- `power_time.py` - times `9 ** (9 ** e)` for answer 14.1
  (`results/power_time.txt`).
- `results/formats-c02.txt`, `results/transcript-c02.txt` - listings in
  the book, made with `../formats.py` and `../show_transcript.py`.
- `results/mcp_agent-ollama-calc.txt` - `../../ch13/mcp_agent.py`
  against Ollama's /v1 with `MCP_SERVER=calc`;
  `mcp_agent-ollama-prefix-calculator.txt` - four attempts with the
  prefix `calculator`, all empty.

The fields `answer` and `correct` of the records are those of the grader at
the time of the run. `../summarize.py` grades every transcript again with
the current `final_answer` of `../measure.py`, and the table in the book
comes from its output (`../results-summary.txt`); for
`results/ollama-native.jsonl` without the tool the stored fields say 12 of
24 correct and the summary 14 of 24.

Ollama 0.40.16 is not itself an MCP client (no MCP options in `ollama`,
`ollama run` or `ollama serve`; its documentation mentions MCP only for an
MCP server for its web search). The MCP client is the agent.

Measured on an Apple M1 Ultra (64 GB), macOS, November 2026, with
Ollama 0.40.16 and qwen3:1.7b (8f68893c685c), default options, every
turn limited to 4096 tokens (`num_predict`); Python 3.15.2.
