# Chapter 17: Evaluation Harnesses

Programs, task definitions and recorded results of Chapter 17.

| File | What it is |
|------|------------|
| `tasks/gsm8k_chat.yaml` | lm-eval task: GSM8K for chat models, zero-shot, format in the prompt |
| `gsm.py` | Inspect task: first 100 GSM8K problems, scored on the last number |
| `agent_eval.py` | Inspect task: the eight workspace questions of Chapter 11, solved by `code/ch11/agent.py` |
| `judge.py` | position bias of a judge model on pairs of right and wrong solutions |
| `run_all.sh` | lm-eval and Inspect runs on Gemma 3 1B (Q8_0, Q4_K_M, Q4_0) via llama-server |
| `run_more.sh` | engine swap (one GGUF in Ollama and llama-server), agent runs, two judges |
| `run_hf.sh` | in-process run: ARC-Easy and ARC-Challenge by log-likelihood, Qwen3-1.7B through Transformers (`results/arc-hf-qwen3-1.7b.json`) |
| `analyze.py` | Wilson intervals, repeated runs, pass@k (Algorithm Y), paired comparisons |
| `summarize_more.py` | two harnesses on the same problems, the engine swap, the judges, the agent |
| `replies.py` | form of the lm-eval replies: marker `####`, `\boxed`, neither, repeated lines |
| `echo_probe.py` | one legacy completion request with `echo` and `logprobs`: which tokens get a log-probability (`results/echo-probe.txt`, from llama-server build 12359 with Gemma 3 1B Q8_0) |
| `preds.py` | wraps a diff into one line of a SWE-bench predictions file (exercise 11); `results/swebench-preds/` has four files made with it by hand, no agent's work, and what the harness reported for each |
| `pytest_tally.py` | sorts the failures and errors of a pytest log by the exception that ended them (`results/swebench-gold/*.tally.txt`) |
| `offline_eval.py` | the SWE-bench harness with containers that have no network (exercise 10) |
| `requests_probe.sh` | inside the image of `psf__requests-2317`: the certificates the client trusts, the chain and the replies of httpbin.org, a connection to its port 1 (`results/swebench-gold/requests-probe.txt`) |
| `requests_cabundle.sh` | inside the same image: the gold patch and the harness's `eval.sh` after the repository's certificate file is replaced by the system's, with pytest's slowest tests (`results/swebench-gold/requests-cabundle.txt`) |
| `make_figure.py` | writes `figures/ch17-runs.tex` from `results/` |
| `quiz/` | the local multiple-choice task of exercise 8 |
| `results/` | summaries (CSV, text); `swebench-gold/` and `swebench-preds/`: reports and logs of the SWE-bench runs on two instances; `swebench/`: reports of an earlier gold run, identical to those of `swebench-gold/gold`, and `preds-check.jsonl`, an earlier check of the format that `preds.py` writes |
| `requirements.txt` | Python packages and versions |

Run, from a directory with a virtual environment `venv` that has the
packages of `requirements.txt`:

```sh
VENV=venv OUT=out ./run_all.sh          # about two hours on an M1 Ultra
VENV=venv OUT=out ./run_more.sh
VENV=venv OUT=out-hf ./run_hf.sh        # seven minutes more
venv/bin/python3 analyze.py out results
venv/bin/python3 summarize_more.py out results
python3 replies.py out results
python3 make_figure.py results BOOK/figures/ch17-runs.tex   # in the book's sources
```

The scripts start llama-server on port 8086 (or `$PORT`) and stop it at the
end; they use Ollama's model `gemma3:1b` and leave Ollama running. Raw logs (lm-eval
samples, Inspect `.eval` files, server logs) go to `$OUT` and are not kept here.

No script here counts the replies that stopped at the token limit (208
with the five examples, 155 with the instruction): the samples of lm-eval
carry neither a finish reason nor a token count. `replies.py` gives the
counts that the samples alone support.

The request with `echo` and `logprobs` of the section on the in-process
attachment, against a llama-server that serves the Q8_0 file:

```sh
python3 echo_probe.py http://127.0.0.1:8086/v1 > results/echo-probe.txt
```

SWE-bench (on Linux with Docker), in a virtual environment with
`swebench==5.0.2`. The gold patches of two instances; the second and
third commands repeat the run, the third without network in the
containers:

```sh
python3 -m swebench.harness.run_evaluation \
    -d SWE-bench/SWE-bench_Lite -p gold -id gold \
    -i psf__requests-2317 pallets__flask-4045 --max_workers 2
python3 -m swebench.harness.run_evaluation \
    -d SWE-bench/SWE-bench_Lite -p gold -id gold-again \
    -i psf__requests-2317 pallets__flask-4045 --max_workers 2
python3 offline_eval.py \
    -d SWE-bench/SWE-bench_Lite -p gold -id offline \
    -i psf__requests-2317 pallets__flask-4045 --max_workers 2
```

The harness writes `gold.RUN.json` (label and run identifier) and
`logs/run_evaluation/RUN/gold/INSTANCE/`; `results/swebench-gold/` has
the summaries, the directories `gold`, `gold-again`, and `offline` of
`logs/run_evaluation`, the console output of each run, the network
setting of a container of the first run (`gold.container.txt`, from
`docker inspect`), and the images (`images.txt`, from `docker images
--digests`). The tallies and the two probes of the Requests image, with
`G=logs/run_evaluation/gold/gold/psf__requests-2317`:

```sh
python3 pytest_tally.py logs/run_evaluation/gold/gold/pallets__flask-4045/test_output.txt
IMG=swebench/sweb.eval.x86_64.psf_1776_requests-2317
docker run --rm -v $PWD/requests_probe.sh:/probe.sh:ro,z $IMG bash /probe.sh
docker run --rm -v $PWD/requests_cabundle.sh:/run.sh:ro,z \
    -v $G/patch.diff:/patch.diff:ro,z -v $G/eval.sh:/eval.sh:ro,z \
    $IMG bash /run.sh
```

(`:z` relabels the files for SELinux, as Fedora needs it.)

Predictions of one's own (exercise 11), made by hand in a checkout of
`pallets/flask` at the instance's base commit, `B` below: the gold diff
applied, half of the fix (`results/swebench-preds/half.diff`), no change,
and a sentence of prose in place of a diff. The first is shown in full;
the others differ in the edit and in the label (`half`, `empty`, `prose`):

```sh
git clone https://github.com/pallets/flask && cd flask
B=d8c37f43724cd9fb0870f77877b7c4c7e38a19e0
git checkout $B
git apply ../logs/run_evaluation/gold/gold/pallets__flask-4045/patch.diff
git add -A
git diff --cached $B | python3 ../preds.py pallets__flask-4045 copy \
    > ../preds-copy.jsonl
git reset --hard $B && cd ..
python3 -m swebench.harness.run_evaluation \
    -d SWE-bench/SWE-bench_Lite -p preds-copy.jsonl -id preds \
    -i pallets__flask-4045 --max_workers 1
```

Afterward:

```sh
docker rmi swebench/sweb.eval.x86_64.psf_1776_requests-2317 \
    swebench/sweb.eval.x86_64.pallets_1776_flask-4045
```
