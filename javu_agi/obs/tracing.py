import time
from contextlib import contextmanager


@contextmanager
def span(name: str, recorder=None):
    t0 = time.time()
    try:
        yield
    finally:
        dur = time.time() - t0
        if recorder:
            recorder(name, dur)
