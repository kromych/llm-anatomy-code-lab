# 2026-11-13T22:41:59-08:00 krom2 (Apple M2, 8 cores, Fedora Asahi Remix 44), CPU build b12376 (61dbf4922)
# command: llama-bench -m <HF cache>/gemma-3-1b-it-Q4_K_M.gguf -p 512 -n 128 -r 3
| model                          |       size |     params | backend    | threads |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | ------: | --------------: | -------------------: |
| gemma3 1B Q4_K - Medium        | 762.49 MiB |   999.89 M | CPU        |       8 |           pp512 |        186.68 ± 0.82 |
| gemma3 1B Q4_K - Medium        | 762.49 MiB |   999.89 M | CPU        |       8 |           tg128 |         42.26 ± 2.47 |

build: 61dbf4922 (12376)
