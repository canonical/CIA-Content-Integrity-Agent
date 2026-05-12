import json
import sys
from datetime import datetime


class StructuredLogger:
    def __init__(self, name: str, pretty: bool = True):
        self.name = name
        self.pretty = pretty

    def _emit(self, level: str, message: str, **kwargs):
        record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "logger": self.name,
            "message": message,
        }
        record.update(kwargs)
        if self.pretty:
            parts = [f"[{self.name}]", level, message]
            if kwargs:
                parts.append(json.dumps(kwargs, default=str))
            print(" ".join(parts), file=sys.stderr)
        else:
            print(json.dumps(record, default=str), file=sys.stderr)

    def info(self, message: str, **kwargs):
        self._emit("INFO", message, **kwargs)

    def warn(self, message: str, **kwargs):
        self._emit("WARN", message, **kwargs)

    def error(self, message: str, **kwargs):
        self._emit("ERROR", message, **kwargs)

    def debug(self, message: str, **kwargs):
        self._emit("DEBUG", message, **kwargs)
