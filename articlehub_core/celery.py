import os
from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'articlehub_core.settings')

app = Celery('articlehub_core')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.update(
    beat_scheduler='django_celery_beat.schedulers:DatabaseScheduler'
)
