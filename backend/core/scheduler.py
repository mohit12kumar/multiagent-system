"""
backend/core/scheduler.py

Background Task Scheduler (Zero External Dependencies).
Runs periodic background maintenance tasks (token cleanup, expired review lock release, cache eviction).
"""

import time
import logging
import threading
from typing import Callable, List, Tuple

logger = logging.getLogger(__name__)

class BackgroundScheduler:
    def __init__(self):
        self._tasks: List[Tuple[str, Callable[[], None], float, float]] = []
        self._running = False
        self._thread: threading.Thread = None
        self._lock = threading.Lock()

    def add_task(self, name: str, fn: Callable[[], None], interval_seconds: float):
        with self._lock:
            self._tasks.append((name, fn, interval_seconds, time.time()))
            logger.info(f"[Scheduler] Added background task '{name}' running every {interval_seconds}s.")

    def start(self):
        with self._lock:
            if self._running:
                return
            self._running = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True, name="BackgroundSchedulerThread")
            self._thread.start()
            logger.info("[Scheduler] Background scheduler loop started.")

    def stop(self):
        with self._lock:
            self._running = False

    def _run_loop(self):
        while self._running:
            time.sleep(5.0)
            now = time.time()
            with self._lock:
                for i in range(len(self._tasks)):
                    name, fn, interval, last_run = self._tasks[i]
                    if now - last_run >= interval:
                        try:
                            fn()
                        except Exception as e:
                            logger.error(f"[Scheduler] Task '{name}' raised error: {e}")
                        self._tasks[i] = (name, fn, interval, now)

background_scheduler = BackgroundScheduler()
