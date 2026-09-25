"""
Centralised logging configuration for ServiceDesk-AI.

All modules should import `logger` from here rather than calling
`logging.getLogger(__name__)` individually, so log format and level
can be changed in one place.

Phase 2+ will add structured JSON logging and log-shipping to a monitoring
service (e.g. Datadog, ELK stack).
"""

import logging
import sys


def get_logger(name: str = "servicedesk") -> logging.Logger:
    """Return a configured logger instance."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="[%(asctime)s] %(levelname)s %(name)s — %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(logging.DEBUG)
    return logger


# Default logger — import this in other modules:
#   from app.utils.logger import logger
logger = get_logger("servicedesk")
