# Number forms over MCP (Chapter 14, "Tools for exact arithmetic")

- `numbers_server.py` - stdio MCP server (standard library only) with the
  tools `affine_form(n, a, b)`, `mod(n, m)` and `is_prime(n)`; it reuses
  the protocol code of `../../ch13/files_server.py`.
- `make_questions.py` - writes `questions.json`: 20 questions "is n of the
  form a*x + b with integer x >= 0?", 10 yes and 10 no, n of 7-8 digits.
- `results/llama-server.jsonl` - `../measure.py` against llama-server,
  2 runs; `results/ollama-v1.jsonl` - against Ollama's /v1, 1 run.
- `results/mcp_agent-llama-server.txt` - one run of
  `../../ch13/mcp_agent.py`.

The fields `answer` and `correct` of the records are those of the grader at
the time of the run. `../summarize.py` grades every transcript again with
the current `final_answer` of `../measure.py`, and the table in the book
comes from its output (`../results-summary.txt`); for
`results/llama-server.jsonl` without tools the stored fields say 16 of 40
correct and the summary 21 of 40.

Measured on an Apple M1 Ultra (64 GB), macOS, November 2026:
llama-server 1.0.0 (build 12359, b1b770d90) with
ggml-org/Qwen3-1.7B-GGUF (Q4_K_M) on port 8083, default sampling
(temperature 0.8, top-k 40, top-p 0.95, min-p 0.05); Ollama 0.40.16 with
qwen3:1.7b (8f68893c685c) and its default options; Python 3.15.2.
Every model turn was limited to 4096 tokens, thinking included.

Reproduce (from `code/ch14`, with both engines running):

    llama-server -hf ggml-org/Qwen3-1.7B-GGUF --port 8083
    ./run_measurements.sh
    python3 summarize.py numbers/results/*.jsonl calculator/results/*.jsonl
