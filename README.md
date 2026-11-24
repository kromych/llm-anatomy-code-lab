# Code and lab supplement of *Anatomy of the Open-Source LLM Stack*

The programs that the book prints or cites, with their small inputs and
recorded results, and the raw measurements of the book's lab. Listings in
the book are copied from these files, and the build of the book checks that
the two agree.

- `code/chNN/` - programs, small inputs and recorded results of Chapter NN
- `code/appA/`, `code/appB/`, `code/appC/` - the scripts of the appendices
  (version check, inventory and snapshot, the examples of the crash course)
- `code/lab/` - scripts used for the lab-machine installs and benchmarks
- `lab/bench/` - raw measurements and the programs that took them
- `lab/hosts/<host>/` - notes, logs and footprints of each lab machine
- `lab/reference/` - figures that vendors publish, with their sources

Table A.1 of the book maps the host names (`xps-8930`, `krom2`, `krom1u`,
`kromyrzen`, `kr0m-gpu`) to the labels S1 to S5 by which the chapters refer to
the machines. In the records, the account under which the lab ran is written
`labuser`, the addresses of the lab's own network are written
`192.168.88.x`, and the scratch directory of a working session is written
`/tmp/scratch`.

## Running the programs

The programs need Python 3.11 or later. Most use the standard library alone;
a chapter that needs more says so in its README, `requirements.txt`, or
Table A.2 of the book. Use a virtual environment (`python3 -m venv venv`, or
`uv venv`), never the system Python. Commands are written as
`python3 script.py`; on Windows the command is `python`. Programs that talk to
a model server take the server's address on the command line, as a base URL
such as `http://127.0.0.1:8080/v1`, which a few of them use as the default.
Write `127.0.0.1` there: on Windows `localhost` resolves to `::1` first and
costs about two seconds per request (Appendix A, Troubleshooting).

Large files (virtual environments, source checkouts, model files, images)
are left out on purpose; the programs download what they need into the
Hugging Face cache or a directory they name.

A few programs write figures or tables of the book from the results kept
here (`code/ch07/mkvendor.py`, `code/ch08/mkisa.py`, `code/ch12/mkport.py`,
`lab/bench/transport/mkfig.py`, and others whose first lines say so). They
take the file to write as an argument; it lies in the book's sources, which
are not part of this repository.

## Files from other projects

Some directories hold small configuration files copied from model
repositories on Hugging Face, so that the programs run without a download,
and the logs of test suites of other projects. `NOTICE.md` lists them with
their origins and licenses. The book reads the source of llama.cpp, vLLM,
SGLang and other projects at the commits its bibliography cites; copies of
those sources are not kept here.

## License

Copyright © 2026 Roman Kisel. The programs and data of the supplement
(`code/` and `lab/`) are released under the MIT License; its text is in
`LICENSE`. The files from other projects listed in `NOTICE.md` remain under
their own licenses.
