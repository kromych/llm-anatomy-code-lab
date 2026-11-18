# Files from other projects

The files below were copied from, or produced by running, other projects.
They are not covered by the MIT License of this repository; each remains
under the license of its origin.

## Configuration files and chat templates of models

Copied from the model repositories on Hugging Face that the directory or
file names carry, so that the programs run without a download. The model
card of each repository states its license.

| Files | Repository | License |
|---|---|---|
| `code/ch02/dl-qwen/index.json`, `code/ch03/dl-Qwen_Qwen3-8B/`, `code/ch03/dl-ollama_qwen3-1.7b/` (as Ollama's `qwen3:1.7b` carries them), `code/ch03/inputs/qwen3-excerpt.jinja` (an excerpt), `code/ch05/qwen3/config.json`, `code/ch06/cfg/Qwen_Qwen3-*.json` | the Qwen3 repositories of Qwen (Qwen/Qwen3-0.6B, Qwen/Qwen3-1.7B, Qwen/Qwen3-8B, Qwen/Qwen3-32B) | Apache License 2.0 |
| `code/ch03/dl-mistralai_Mistral-7B-Instruct-v0.3/`, `code/ch06/cfg/mistralai_Mistral-7B-v0.1.json` | mistralai/Mistral-7B-Instruct-v0.3, mistralai/Mistral-7B-v0.1 | Apache License 2.0 |
| `code/ch03/dl-unsloth_Mistral-Nemo-Instruct-2407/` | unsloth/Mistral-Nemo-Instruct-2407 (a copy of mistralai/Mistral-Nemo-Instruct-2407) | Apache License 2.0 |
| `code/ch03/dl-openai-community_gpt2/` | openai-community/gpt2 | MIT License |
| `code/ch03/dl-openai_gpt-oss-20b/`, `code/ch06/cfg/openai_gpt-oss-20b.json` | openai/gpt-oss-20b | Apache License 2.0 |
| `code/ch05/model/` | HuggingFaceTB/SmolLM2-135M | Apache License 2.0 |
| `code/ch06/cfg/deepseek-ai_DeepSeek-V3.json` | deepseek-ai/DeepSeek-V3 | as its model card states |
| `code/ch03/dl-unsloth_Llama-3.1-8B-Instruct/`, `code/ch06/cfg/unsloth_Meta-Llama-3.1-*.json` | unsloth/Llama-3.1-8B-Instruct, unsloth/Meta-Llama-3.1-8B-Instruct, unsloth/Meta-Llama-3.1-70B-Instruct (copies of Meta's repositories) | Llama 3.1 Community License |
| `code/ch03/dl-unsloth_gemma-3-1b-it/`, `code/ch06/cfg/unsloth_gemma-3-27b-it.json` | unsloth/gemma-3-1b-it, unsloth/gemma-3-27b-it (copies of Google's repositories) | Gemma Terms of Use |

Llama 3.1 is licensed under the Llama 3.1 Community License, Copyright ©
Meta Platforms, Inc. All Rights Reserved. The license is at
<https://www.llama.com/llama3_1/license/>.

Gemma is provided under and subject to the Gemma Terms of Use found at
<https://ai.google.dev/gemma/terms>.

## Logs of other projects' test suites

`code/ch17/results/swebench*/` holds reports and logs that the SWE-bench
harness (MIT License) wrote while it ran the tests of two task instances.
The logs quote test names, tracebacks and source lines of
[psf/requests](https://github.com/psf/requests) (Apache License 2.0) and
[pallets/flask](https://github.com/pallets/flask) (BSD 3-Clause License).

## Outputs of programs

The logs under `lab/hosts/` and the recorded outputs under `code/*/results`
are what llama.cpp, Ollama, vLLM, SGLang and the harnesses of the book
printed on the lab machines; they are kept as measurements.
