import logging


def get_logger(name: str | None = None):
    """Return a module-scoped logger.

    If `name` is not provided, the calling module's name will be used.
    """
    if name:
        return logging.getLogger(name)
    return logging.getLogger(f"app.{__name__}")
