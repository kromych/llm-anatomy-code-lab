# Searching the web over MCP (Chapter 14, "Searching the web")

- `settings.yml` - the settings of a private SearXNG that differ from the
  defaults: JSON output enabled, limiter off, a secret key to fill in.
- `search_server.py` - stdio MCP server (standard library only, protocol of
  `../../ch13/files_server.py`) with `web_search(query, max_results)` and
  `fetch_page(url, max_chars)`. `fetch_page` admits only http and https
  URLs whose host resolves to global addresses, checks every redirect,
  reads at most 1 MB in 15 s, accepts HTML and plain text, and marks the
  page as untrusted. Set `SEARXNG_URL` (default http://127.0.0.1:8888).
- `search_run.py` - the agent loop of `../../ch13/mcp_agent.py`, recording
  each conversation in a JSONL file and printing it as the book's
  listings.
- `cite_check.py` - answer 14.3: sorts the URLs of each recorded answer
  into read, seen (search results only) and unseen.
- `results/run-qwen3-8b.jsonl` - six runs, 2026-11-14 (first: the release
  question answered from snippets; then the announcement question five
  times), with the text of fetched pages removed from the record (first
  two lines and length kept); `results/transcript-run6.txt` - the
  listing in the book, made before the removal;
  `results/mcp_agent-run.txt`, `results/mcp_agent-run2.txt` - two runs
  of the command of the book with `../../ch13/mcp_agent.py`;
  `results/cite_check.txt`.

Set-up used: SearXNG 2026.11.14+a7128d5d1 (docker.io/searxng/searxng:latest)
on xps-8930 (Docker 29.9.2), published on 127.0.0.1:8888 there and reached
from the Mac through `ssh -f -N -L 127.0.0.1:8888:127.0.0.1:8888`;
Qwen3-8B Q8_0 on llama-server 1.0.0 (build 12359), port 8090, sampling
--temp 0.6 --top-p 0.95 --top-k 20 --min-p 0; Python 3.15.2.

Notes for the operator of such an instance:

- The container takes ownership of `config/` when it starts, so put
  `settings.yml` there first; later changes need sudo.
- Of the engines that the image enables for general searches, Brave,
  DuckDuckGo and Google (through its Custom Search Engine, used without a
  key) answered our first queries. They do not always answer: within an
  hour DuckDuckGo had asked for a CAPTCHA and Brave had suspended our
  address for too many requests. SearXNG reports such engines in the field
  `unresponsive_engines` of its JSON reply, and `web_search` repeats them
  in the first line of its result.
- The engines for Wikipedia and Wikidata never started. SearXNG requires a
  contact address, `general.contact_url`, before it uses them, to comply
  with the policies of those services; we left it empty, since it would
  identify the operator of the instance to them.

Stop: `docker rm -f searxng` on the host, and end the SSH tunnel.
