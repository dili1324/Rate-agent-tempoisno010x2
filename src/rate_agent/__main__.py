from __future__ import annotations

import logging
import sys

from rate_agent.app import run
from rate_agent.config import ConfigError, Settings
from rate_agent.logging_config import configure_logging


def main() -> int:
    configure_logging()
    logger = logging.getLogger("rate_agent")
    try:
        run(Settings.from_env())
    except ConfigError as exc:
        logger.error("%s", exc)
        return 2
    except Exception:
        logger.exception("Rate Agent failed")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
