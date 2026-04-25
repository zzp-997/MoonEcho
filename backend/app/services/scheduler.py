from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler


class SchedulerManager:
    def __init__(self) -> None:
        self.scheduler = BackgroundScheduler()
        self.started_count = 0
        self.shutdown_count = 0
        self.is_running = False

    def start(self) -> None:
        self.started_count += 1
        if not self.scheduler.running:
            self.scheduler.start()
        self.is_running = True

    def shutdown(self) -> None:
        self.shutdown_count += 1
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
        self.is_running = False
