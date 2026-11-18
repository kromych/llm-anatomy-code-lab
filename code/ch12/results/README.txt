output_typed-qwen3-8b.txt, output_typed-qwen3-8b.jsonl
output_typed-qwen3-1.7b.txt, output_typed-qwen3-1.7b.jsonl
    The output of output_typed.py and the proxy's log of its requests (the
    tags end in -dump, so each line holds the request in full), with
      llama-server -hf ggml-org/Qwen3-8B-GGUF:Q8_0 --port 8107 \
        --temp 0 --seed 1 --reasoning off -n 1024
    and with ggml-org/Qwen3-1.7B-GGUF:Q4_K_M in its place:
      python3 proxy.py 8182 http://127.0.0.1:8107 LOG &
      python3 output_typed.py http://127.0.0.1:8182
    llama-server 1.0.0 (build 12359, commit b1b770d90) on S3-macOS,
    Python 3.14.10, pydantic-ai-slim 2.68.0, openai-agents 0.24.0.
    Not yet run against Ollama:
      AGENT_MODEL=qwen3:1.7b python3 output_typed.py http://127.0.0.1:8182
    with the proxy pointed at http://127.0.0.1:11434.

../run-1.7b-rerun/
    ./run_exp.sh run-1.7b-rerun, with the server command at the head of
    that script (Qwen3 1.7B) and the packages of requirements.txt. The
    machine was busy, so its seconds measure nothing. The rows of the
    hand-written loop, PydanticAI and the Agents SDK agree with
    ../run-1.7b in every column but the times; smolagents differs
    (8 correct, 3.89 requests, 10,214 prompt and 989 completion tokens per
    task, 15 capped requests).

../run2-1.7b/, ../run2-8b/
    The runs that Chapter 12 reports. Each is one call of
      ./run_exp.sh 1.7b run2-1.7b        ./run_exp.sh 8b run2-8b
    on S3-macOS, held under code/lab/mac-lockrun.py exclusive. The script
    starts llama-server itself with the command line that it contains,
    runs the five programs three times through proxy.py, makes the probes,
    and stops the engine.
      results.jsonl       one line per answer (runner.py)
      proxy-run.jsonl     one line per request: sizes, usage, finish reason
      proxy-full.jsonl.gz the same lines with request and reply in full
      server.log          the engine's log, with its timings
      runner.log, proxy.err   what the programs wrote besides
      versions.txt, packages.txt, props.json, load.txt
                          the engine, the packages of the virtual
                          environment, the engine's /props, and uptime at
                          the start, after the repetitions, and at the end
                          (the first line still averages over the workload
                          that held the lock before)
      determinism.txt, replay.txt, trace_pyd.txt   the probes
      summary.json, tasks.tsv   written afterward by python3 analyze.py RUN
    python3 mkport.py turns the two summaries into the rows of the table
    and into figures/ch12-port.tex.

../run2-1.7b/nolimit/
    ./nolimit.sh 1.7b run2-1.7b: the engine without -n 1024, and the first
    capped request of smolagents sent to it again (replay.py ... capped).
    The reply ran for 39,165 tokens, until the context was full.

../run2-1.7b-first/
    An earlier call of ./run_exp.sh 1.7b, kept as one more repetition. The
    experiment is the same; the script then left proxy-full.jsonl
    uncompressed (compressed afterward by hand with gzip -9), and the
    probes were earlier versions: determinism.py compared the cached runs
    with each other, and replay.py sent the capped request alone. The rows
    of the four programs other than smolagents equal those of run2-1.7b
    in every column but the times.

dspy_default.txt, dspy_default.jsonl
    python3 dspy_default.py http://127.0.0.1:8182/dspy-default/v1, the
    DSPy port without model_type="chat", through proxy.py against the
    engine of run_exp.sh with the smaller model: both requests went to
    /v1/responses; llama-server answered the first with status 200 and the
    second, which carries the history, with status 400.
