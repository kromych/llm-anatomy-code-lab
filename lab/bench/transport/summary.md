# Round trips measured for figures/transports.tex

Median of each test, in microseconds; raw files in results/. Machines:

- krom1u: Apple M1 Ultra, macOS 27.2
- xps-8930: Core i7-8700, Fedora 44
- krom2: Apple M2, Fedora Asahi 44
- kromyrzen: Ryzen 7 3700X, Windows 11
- kr0m-gpu: 8 x NVIDIA H100 PCIe, Ubuntu 24.04

| row | test | machine | median |
|---|---|---|---|
| Function call, FFI | call | krom1u | 0.043 us |
| Function call, FFI | call | krom2 | 0.049 us |
| Function call, FFI | call | kromyrzen | 0.063 us |
| Function call, FFI | call | xps-8930 | 0.051 us |
| Function call, FFI | ctypes | krom1u | 0.306 us |
| Function call, FFI | ctypes | krom2 | 0.263 us |
| Function call, FFI | ctypes | kromyrzen | 0.426 us |
| Function call, FFI | ctypes | xps-8930 | 0.37 us |
| A page of a mapped model file | mmap-cold | krom1u | 109.75 us |
| A page of a mapped model file | mmap-cold | krom2 | 109.459 us |
| A page of a mapped model file | mmap-cold | xps-8930 | 96.611 us |
| A page of a mapped model file | mmap-hot | krom1u | 0.208 us |
| A page of a mapped model file | mmap-hot | krom2 | 0.417 us |
| A page of a mapped model file | mmap-hot | kromyrzen | 0.1 us |
| A page of a mapped model file | mmap-hot | xps-8930 | 0.267 us |
| A page of a mapped model file | mmap-warm | krom1u | 1.25 us |
| A page of a mapped model file | mmap-warm | krom2 | 2.792 us |
| A page of a mapped model file | mmap-warm | kromyrzen | 1.3 us |
| A page of a mapped model file | mmap-warm | xps-8930 | 3.034 us |
| Shared memory | shm | krom1u | 0.333 us |
| Shared memory | shm | krom2 | 0.333 us |
| Shared memory | shm | kromyrzen | 0.6 us |
| Shared memory | shm | xps-8930 | 0.485 us |
| Pipes and stdio | stdio | krom1u | 30 us |
| Pipes and stdio | stdio | krom2 | 41 us |
| Pipes and stdio | stdio | kromyrzen | 49.1 us |
| Pipes and stdio | stdio | xps-8930 | 23.955 us |
| Unix or TCP socket, named pipe, ZeroMQ | mpconn | krom1u | 8.541 us |
| Unix or TCP socket, named pipe, ZeroMQ | mpconn | krom2 | 19.791 us |
| Unix or TCP socket, named pipe, ZeroMQ | mpconn | kromyrzen | 21.8 us |
| Unix or TCP socket, named pipe, ZeroMQ | mpconn | xps-8930 | 10.551 us |
| Unix or TCP socket, named pipe, ZeroMQ | tcp | krom1u | 25.041 us |
| Unix or TCP socket, named pipe, ZeroMQ | tcp | krom2 | 19.125 us |
| Unix or TCP socket, named pipe, ZeroMQ | tcp | kromyrzen | 24.4 us |
| Unix or TCP socket, named pipe, ZeroMQ | tcp | xps-8930 | 13.523 us |
| Unix or TCP socket, named pipe, ZeroMQ | unix | krom1u | 11.875 us |
| Unix or TCP socket, named pipe, ZeroMQ | unix | krom2 | 10.292 us |
| Unix or TCP socket, named pipe, ZeroMQ | unix | xps-8930 | 8.151 us |
| Unix or TCP socket, named pipe, ZeroMQ | zmq-ipc | krom1u | 50.875 us |
| Unix or TCP socket, named pipe, ZeroMQ | zmq-ipc | krom2 | 88.333 us |
| Unix or TCP socket, named pipe, ZeroMQ | zmq-ipc | xps-8930 | 20.719 us |
| Unix or TCP socket, named pipe, ZeroMQ | zmq-tcp | krom1u | 83.062 us |
| Unix or TCP socket, named pipe, ZeroMQ | zmq-tcp | krom2 | 75.458 us |
| Unix or TCP socket, named pipe, ZeroMQ | zmq-tcp | kromyrzen | 121.7 us |
| Unix or TCP socket, named pipe, ZeroMQ | zmq-tcp | xps-8930 | 30.936 us |
| XPC, COM/ALPC, D-Bus | dbus | krom2 | 71.125 us |
| XPC, COM/ALPC, D-Bus | dbus | xps-8930 | 77.826 us |
| XPC, COM/ALPC, D-Bus | xpc | krom1u | 22.125 us |
| HTTP on loopback, with SSE | http | krom1u | 103.625 us |
| HTTP on loopback, with SSE | http | krom2 | 203.25 us |
| HTTP on loopback, with SSE | http | kromyrzen | 174.6 us |
| HTTP on loopback, with SSE | http | xps-8930 | 149.156 us |
| HTTP on loopback, with SSE | llama-server | krom1u | 71.708 us |
| HTTP on loopback, with SSE | ollama | krom1u | 85.667 us |
| HTTP on loopback, with SSE | ollama | xps-8930 | 96.721 us |
| HTTP on loopback, with SSE | sse | krom1u | 106.125 us |
| HTTP on loopback, with SSE | sse | krom2 | 208.625 us |
| HTTP on loopback, with SSE | sse | kromyrzen | 177.4 us |
| HTTP on loopback, with SSE | sse | xps-8930 | 154.749 us |
| TCP and HTTP in a LAN | lan-http | krom2 | 595.459 us |
| TCP and HTTP in a LAN | lan-tcp | krom2 | 142.709 us |
| HTTPS over the internet | https | krom1u:https-github.com | 9729.81 us |
| HTTPS over the internet | https | krom1u:https-huggingface.co | 4750.08 us |
| PCIe DMA | pcie-4k | kr0m-gpu | 12.459 us |
| NVLink, Infinity Fabric, RDMA | allreduce-pair | kr0m-gpu | 54.7 us |
