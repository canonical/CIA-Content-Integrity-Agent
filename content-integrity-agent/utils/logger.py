"""
StructuredLogger: Structured logging for the entire system.
ENGINEER A: Implement this utility.
"""

class StructuredLogger:
    """Prints structured JSON lines to stderr, pretty-printed to stdout."""

    def __init__(self, name: str, pretty: bool = True):
        self.name = name
        self.pretty = pretty

    def info(self, message: str, **kwargs):
        raise NotImplementedError("Engineer A: Implement info logging")

    def warn(self, message: str, **kwargs):
        raise NotImplementedError("Engineer A: Implement warn logging")

    def error(self, message: str, **kwargs):
        raise NotImplementedError("Engineer A: Implement error logging")

    def debug(self, message: str, **kwargs):
        raise NotImplementedError("Engineer A: Implement debug logging")
