from celery import Celery

from app.config import settings

celery_app = Celery(
    "finsight",
    broker=settings.redis_url,
    backend=settings.redis_url,
    # A `celery -A app.celery_app worker` only imports this module — without
    # `include`, app/tasks.py (and its @celery_app.task decorator) never
    # runs, so the worker starts up with zero tasks registered.
    include=["app.tasks"],
)
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]
