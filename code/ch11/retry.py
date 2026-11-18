# retry.py -- repeat step N2 after overload, server errors and timeouts.
import http.client, time, urllib.error

def patient(chat, tries=5, first=1.0):
    def wrapped(messages, *args, **kwargs):
        wait = first
        for attempt in range(1, tries + 1):
            try:
                return chat(messages, *args, **kwargs)
            except urllib.error.HTTPError as e:      # the server answered
                if (e.code != 429 and e.code < 500) or attempt == tries:
                    raise                            # a mistake of ours
                after = e.headers.get("Retry-After", "")
                delay = float(after) if after.isdigit() else wait
            except (urllib.error.URLError, TimeoutError, ConnectionError,
                    http.client.HTTPException):
                if attempt == tries:                 # no complete answer
                    raise
                delay = wait
            print(f"[attempt {attempt} failed; waiting {delay:g} s]")
            time.sleep(delay)
            wait *= 2
    return wrapped
