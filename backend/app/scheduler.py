from __future__ import annotations

import logging
import os
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from .database import session_scope
from .reporting import get_form_report

logger = logging.getLogger(__name__)


class ReportScheduler:
    def __init__(self, interval_minutes: int = 60):
        self.interval_minutes = interval_minutes
        self.scheduler = BackgroundScheduler()
        self.scheduler.configure(timezone="UTC")

    def start(self) -> None:
        if not self.scheduler.running:
            self.scheduler.start()

    def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown()

    def schedule_for_form(self, form_id: int) -> None:
        job_id = f"form-report-{form_id}"
        if self.scheduler.get_job(job_id):
            return
        self.scheduler.add_job(
            func=_generate_report_job,
            trigger="interval",
            minutes=self.interval_minutes,
            id=job_id,
            kwargs={"form_id": form_id},
            replace_existing=True,
        )


def _generate_report_job(form_id: int) -> None:
    logger.info("Generating scheduled report for form %s at %s", form_id, datetime.utcnow())
    with session_scope() as session:
        try:
            report = get_form_report(session, form_id)
            logger.info("Generated report summary: %s", report.summary)
        except ValueError:
            logger.warning("Scheduled report skipped; form %s not found", form_id)


def configure_report_scheduler() -> ReportScheduler | None:
    enable_scheduler = os.getenv("ENABLE_REPORT_SCHEDULER", "false").lower() == "true"
    if not enable_scheduler:
        return None
    interval = int(os.getenv("REPORT_SCHEDULER_INTERVAL", "60"))
    scheduler = ReportScheduler(interval_minutes=interval)
    scheduler.start()
    return scheduler
