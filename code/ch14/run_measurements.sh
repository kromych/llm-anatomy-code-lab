#!/bin/sh
# run_measurements.sh: the measurements of Section 14.1 ("tools for exact
# arithmetic"), one after another so that the engines do not compete.
# Needs llama-server on port 8083 and `ollama serve` on port 11434.
set -e
cd "$(dirname "$0")"
L=http://127.0.0.1:8083/v1
O=http://127.0.0.1:11434
python3 measure.py numbers/questions.json openai $L any \
    numbers/results/llama-server.jsonl --runs 2 --server-name numbers \
    -- python3 numbers/numbers_server.py
python3 measure.py calculator/questions.json ollama $O qwen3:1.7b \
    calculator/results/ollama-native.jsonl --runs 2 \
    --server-name calculator -- python3 calculator/calc_server.py
python3 measure.py numbers/questions.json openai $O/v1 qwen3:1.7b \
    numbers/results/ollama-v1.jsonl --runs 1 --server-name numbers \
    -- python3 numbers/numbers_server.py
python3 measure.py calculator/questions.json openai $O/v1 qwen3:1.7b \
    calculator/results/ollama-v1-tools.jsonl --runs 2 --modes tools \
    --server-name calculator -- python3 calculator/calc_server.py
python3 measure.py calculator/questions.json openai $L any \
    calculator/results/llama-server-tools.jsonl --runs 2 --modes tools \
    --server-name calculator -- python3 calculator/calc_server.py
python3 measure.py calculator/questions.json ollama $O qwen3:1.7b \
    calculator/results/ollama-native-calc.jsonl --runs 2 --modes tools \
    --server-name calc -- python3 calculator/calc_server.py
echo done
