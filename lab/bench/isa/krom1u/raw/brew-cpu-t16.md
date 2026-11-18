| model                          |       size |     params | backend    | threads | dev          |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | ------: | ------------ | --------------: | -------------------: |
| gemma3 1B Q4_0                 | 682.24 MiB |   999.89 M | BLAS,MTL   |      16 | none         |           pp512 |      1060.69 ± 79.80 |
| gemma3 1B Q4_0                 | 682.24 MiB |   999.89 M | BLAS,MTL   |      16 | none         |           tg128 |        143.35 ± 1.46 |
| gemma3 1B Q8_0                 | 1013.54 MiB |   999.89 M | BLAS,MTL   |      16 | none         |           pp512 |       847.33 ± 39.66 |
| gemma3 1B Q8_0                 | 1013.54 MiB |   999.89 M | BLAS,MTL   |      16 | none         |           tg128 |        119.78 ± 1.97 |
| gemma3 1B Q4_K - Medium        | 762.49 MiB |   999.89 M | BLAS,MTL   |      16 | none         |           pp512 |       710.14 ± 31.06 |
| gemma3 1B Q4_K - Medium        | 762.49 MiB |   999.89 M | BLAS,MTL   |      16 | none         |           tg128 |        126.14 ± 1.43 |
