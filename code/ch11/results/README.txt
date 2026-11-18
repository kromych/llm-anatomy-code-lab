Recordings made after the programs of Chapter 11 were changed (the field
"model" in every request, 127.0.0.1, portable tools.py, show.py reading
questions from standard input, agent.run continuing a conversation).
The recordings in the parent directory (session-*.jsonl, eval-*.jsonl,
var-*.jsonl, protocols/) were made with the earlier programs and are kept
as they are.

Engine: llama-server "version: 1.0.0 (build 12359, commit b1b770d90),
built with AppleClang 21.0.0.21000401 for Darwin arm64", from Homebrew, on
S3-macOS; Python 3.15.2. Unless a line below says otherwise the server was
started as in the chapter, on another port:
  llama-server -hf ggml-org/Qwen3-1.7B-GGUF:Q4_K_M --host 127.0.0.1 --port 8107
The machine was busy with other work, so the seconds and milliseconds in
these files measure nothing; the token counts and the texts do.

session-plain-rerun.jsonl, session-compact-rerun.jsonl
    python3 session.py http://127.0.0.1:8107/v1 plain    (and: compact)
    The server was restarted before each run. All twenty requests of each
    run have the prompt, cached, computed and completion tokens and the
    answers of ../session-plain.jsonl and ../session-compact.jsonl:
    33,765 / 31,134 / 2,631 / 459 and 27,478 / 24,305 / 3,173 / 462.
eval-native-rerun.jsonl
    python3 evaluate.py http://127.0.0.1:8107/v1   (fresh server)
    4 of 8 solved, 18 turns, 7,958 prompt and 486 completion tokens, the
    answers of ../eval-native-llama.jsonl.
tryit.txt, show.txt
    The question of the Try it box through agent.py and through show.py.
overflow-llama-server.txt
    python3 overflow.py http://127.0.0.1:8107/v1
estimate.txt
    python3 estimate.py http://127.0.0.1:8107/v1
test_guard.txt
    python3 test_guard.py   (no model; a scripted server)
guard-session-c2048.txt
    python3 exp_guard.py http://127.0.0.1:8107/v1
    with the server started with  -c 2048 -np 1
unguarded-n20.txt, unguarded-n8.txt
    python3 unguarded.py http://127.0.0.1:8107/v1
    with the server started with  -n 20  and with  -n 8
test_search_notes.txt
    python3 test_search_notes.py   (no model; mock.py and a stub)
test_search_notes-qwen3.txt
    python3 test_search_notes.py http://127.0.0.1:8107/v1
    Qwen3 1.7B as the chat model, the stub in place of the embeddings.
search_notes-qwen3-embedding.txt
    EMBED_BASE=http://127.0.0.1:8107/v1 python3 search_notes.py QUERY...
    with the server started as
      llama-server -hf Qwen/Qwen3-Embedding-0.6B-GGUF:Q8_0 --embeddings \
        --host 127.0.0.1 --port 8107
tool_cost.txt
    python3 tool_cost.py http://127.0.0.1:8107/v1

Recordings for the answers to Exercises 11.5 to 11.7 (the same engine, on
port 8107; Ollama 0.40.16 with qwen3:1.7b on port 11434):

nostop.txt
    python3 nostop.py http://127.0.0.1:8107/v1
    react.py without its stop sequence on the eight tasks: none solved,
    nine replies, eight of them with an Observation line of the model's own.
test_parallel.txt
    python3 test_parallel.py   (no model; mock.py)
unanswered-llama-server.txt, unanswered-ollama.txt
    python3 unanswered.py http://127.0.0.1:8107/v1 default
    python3 unanswered.py http://127.0.0.1:11434/v1 qwen3:1.7b
session-z5-rerun.jsonl
    python3 exp_z5.py http://127.0.0.1:8107/v1   (fresh server, -lv 5)
    All twenty requests and the summarizing request have the tokens and
    the answers of ../session-z5.jsonl.
z5-server-log.txt
    The server's log of that run from the end of request 13 to the start of
    request 14 (the lines about the prompt cache need -lv 4 or more; the
    default level leaves them out): the slot of 1,858 tokens saved to the
    prompt cache and
    cleared, and the saved prompt found with 349 common tokens
    (f_keep = 0.188) and left where it was.
