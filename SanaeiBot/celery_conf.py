from celery import Celery
from os import environ
from datetime import timedelta

environ.setdefault('DJANGO_SETTINGS_MODULE', 'SanaeiBot.settings')

celery_app = Celery('SanaeiBot')


celery_app.conf.broker_connection_retry_on_startup = True
celery_app.autodiscover_tasks()
celery_app.conf.broker_url = environ.get("CELERY_BROKER_URL")
celery_app.conf.result_backend = environ.get("CELERY_RESULT_BACKEND")
celery_app.conf.task_serializer = 'json'
# celery_app.conf.result_expires = timedelta(hours=1)
