from __future__ import annotations

import logging
from contextlib import contextmanager
from time import perf_counter
from typing import Iterator


@contextmanager
def timed_step(logger: logging.Logger, step_name: str) -> Iterator[None]:
    start = perf_counter()
    logger.info("Starting step: %s", step_name)
    try:
        yield
    except Exception:
        elapsed_ms = (perf_counter() - start) * 1000
        logger.exception("Step failed: %s duration_ms=%.2f", step_name, elapsed_ms)
        raise
    else:
        elapsed_ms = (perf_counter() - start) * 1000
        logger.info("Completed step: %s duration_ms=%.2f", step_name, elapsed_ms)
