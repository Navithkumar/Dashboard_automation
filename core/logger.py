"""Logging system supporting rotating file logs and live SSE queue broadcasting."""
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from config.settings import settings


class LogBroadcaster:
    """Singleton message bus for streaming automation logs to web clients."""

    def __init__(self):
        self._listeners: Dict[str, List[asyncio.Queue]] = {}
        self._history: Dict[str, List[dict]] = {}

    def register(self, run_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        if run_id not in self._listeners:
            self._listeners[run_id] = []
        self._listeners[run_id].append(queue)

        # Replay existing history to new listener
        if run_id in self._history:
            for item in self._history[run_id]:
                try:
                    queue.put_nowait(item)
                except asyncio.QueueFull:
                    pass
        return queue

    def unregister(self, run_id: str, queue: asyncio.Queue):
        if run_id in self._listeners and queue in self._listeners[run_id]:
            self._listeners[run_id].remove(queue)
            if not self._listeners[run_id]:
                self._listeners.pop(run_id, None)

    def broadcast(self, run_id: str, message: str, level: str = "INFO", step: Optional[str] = None):
        log_entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "level": level,
            "step": step or "General",
            "message": message,
        }

        if run_id not in self._history:
            self._history[run_id] = []
        self._history[run_id].append(log_entry)

        if run_id in self._listeners:
            for q in list(self._listeners[run_id]):
                try:
                    q.put_nowait(log_entry)
                except asyncio.QueueFull:
                    pass

    def get_history(self, run_id: str) -> List[dict]:
        return self._history.get(run_id, [])

    def cleanup(self, run_id: str):
        self._listeners.pop(run_id, None)


broadcaster = LogBroadcaster()


class RunLogger:
    """Contextual logger bound to an automation run."""

    def __init__(self, run_id: str, logger: logging.Logger):
        self.run_id = run_id
        self.logger = logger

    def log(self, message: str, level: str = "INFO", step: Optional[str] = None):
        formatted = f"[{step}] {message}" if step else message
        if level == "DEBUG":
            self.logger.debug(formatted)
        elif level == "WARNING":
            self.logger.warning(formatted)
        elif level == "ERROR":
            self.logger.error(formatted)
        else:
            self.logger.info(formatted)

        broadcaster.broadcast(self.run_id, message, level=level, step=step)

    def info(self, message: str, step: Optional[str] = None):
        self.log(message, level="INFO", step=step)

    def debug(self, message: str, step: Optional[str] = None):
        self.log(message, level="DEBUG", step=step)

    def warning(self, message: str, step: Optional[str] = None):
        self.log(message, level="WARNING", step=step)

    def error(self, message: str, step: Optional[str] = None):
        self.log(message, level="ERROR", step=step)


def setup_logger(name: str = "rpa_automation", log_file: Optional[Path] = None) -> logging.Logger:
    """Configures and returns a root-level or named logger with file and console handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler
        if log_file is None:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = settings.logs_dir / f"automation_{ts}.log"

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_run_logger(run_id: str, log_file: Optional[Path] = None) -> RunLogger:
    base_logger = setup_logger(f"run.{run_id}", log_file=log_file)
    return RunLogger(run_id, base_logger)
