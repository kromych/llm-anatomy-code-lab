| model                          |       size |     params | backend    | threads |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | ------: | --------------: | -------------------: |
| gemma3 1B Q4_0                 | 682.24 MiB |   999.89 M | BLAS,MTL   |      16 |           pp512 |      6605.68 ± 22.96 |
| gemma3 1B Q4_0                 | 682.24 MiB |   999.89 M | BLAS,MTL   |      16 |           tg128 |       141.15 ± 17.81 |
| gemma3 1B Q8_0                 | 1013.54 MiB |   999.89 M | BLAS,MTL   |      16 |           pp512 |     6538.98 ± 136.47 |
| gemma3 1B Q8_0                 | 1013.54 MiB |   999.89 M | BLAS,MTL   |      16 |           tg128 |       130.69 ± 34.68 |
| gemma3 1B Q4_K - Medium        | 762.49 MiB |   999.89 M | BLAS,MTL   |      16 |           pp512 |       5724.79 ± 5.58 |
| gemma3 1B Q4_K - Medium        | 762.49 MiB |   999.89 M | BLAS,MTL   |      16 |           tg128 |        186.33 ± 0.51 |
