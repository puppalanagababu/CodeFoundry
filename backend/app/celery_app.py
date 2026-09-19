import os
from celery import Celery
from app.config import settings

celery_app = Celery(
    "codefoundry_fastapi",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.evaluation_tasks"],
)

celery_app.conf.update(task_serializer="json", 
    result_serializer="json", 
    accept_content=["json"],
    timezone="UTC", 
    enable_utc=True, 
    task_track_started=True,
    task_time_limit=60,
    task_soft_time_limit=30,
)
