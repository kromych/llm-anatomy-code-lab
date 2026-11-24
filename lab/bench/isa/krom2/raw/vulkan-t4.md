| model                          |       size |     params | backend    | ngl | threads |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | ------: | --------------: | -------------------: |
| gemma3 1B Q4_0                 | 682.24 MiB |   999.89 M | Vulkan     |  99 |       4 |           pp512 |        626.21 ± 0.28 |
| gemma3 1B Q4_0                 | 682.24 MiB |   999.89 M | Vulkan     |  99 |       4 |           tg128 |         51.68 ± 0.10 |
| gemma3 1B Q8_0                 | 1013.54 MiB |   999.89 M | Vulkan     |  99 |       4 |           pp512 |        588.88 ± 0.57 |
| gemma3 1B Q8_0                 | 1013.54 MiB |   999.89 M | Vulkan     |  99 |       4 |           tg128 |         40.32 ± 0.03 |
| gemma3 1B Q4_K - Medium        | 762.49 MiB |   999.89 M | Vulkan     |  99 |       4 |           pp512 |        567.14 ± 0.51 |
| gemma3 1B Q4_K - Medium        | 762.49 MiB |   999.89 M | Vulkan     |  99 |       4 |           tg128 |         44.31 ± 0.01 |
