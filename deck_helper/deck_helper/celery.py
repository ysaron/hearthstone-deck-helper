import os
from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'deck_helper.settings')

app = Celery('deck_helper')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
