"""
Application Logging Configuration
=================================
Configures structured, security-conscious application logging.
Ensures sensitive credentials, authorization headers, and tokens are never leaked to logs.
"""

import logging
import sys
from typing import Any, Dict


# Keys that must be masked if encountered in logging dictionaries
SENSITIVE_KEYS = {
    "password",
    "hashed_password",
    "token",
    "access_token",
    "secret",
    "secret_key",
    "authorization",
    "credentials",
}


def sanitize_dict_for_logging(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively masks sensitive values (passwords, tokens, keys) in dictionaries.
    """
    sanitized = {}
    for key, value in data.items():
        if isinstance(key, str) and any(s in key.lower() for s in SENSITIVE_KEYS):
            sanitized[key] = "********"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict_for_logging(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_dict_for_logging(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            sanitized[key] = value
    return sanitized


def setup_logging(log_level: str = "INFO") -> None:
    """
    Initializes root application logger with standardized stream formatting.
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    log_format = (
        "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S"

    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        datefmt=date_format,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    # Quiet overly verbose third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("passlib").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Factory function returning a namespaced application logger.
    """
    return logging.getLogger(f"flowgrid.{name}")
