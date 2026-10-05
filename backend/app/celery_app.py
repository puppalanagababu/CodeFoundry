import os
import redis.connection
from redis.maint_notifications import MaintNotificationsConfig
from celery import Celery
from app.config import settings

# Configure universal Redis compatibility (supports Redis 3.x - 7.x without RESP3 requirement)
_orig_abstract_conn_init = redis.connection.AbstractConnection.__init__


def _compat_conn_init(self, *args, **kwargs):
    kwargs.setdefault("protocol", 2)
    return _orig_abstract_conn_init(self, *args, **kwargs)


redis.connection.AbstractConnection.__init__ = _compat_conn_init
redis.connection.MaintNotificationsAbstractConnection._configure_maintenance_notifications = lambda *args, **kwargs: None

celery_app = Celery(
    "codefoundry_fastapi",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.evaluation_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=60,
    task_soft_time_limit=30,
)

