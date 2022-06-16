import os
from celery import Celery
from celery.schedules import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'deck_helper.settings')

app = Celery('deck_helper')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# --- celery beat -------------------------------------------------
app.conf.beat_schedule = {
    'check_for_hs_api_updates': {
        'task': 'core.tasks.check_for_hs_api_updates',
        'schedule': crontab(minute=0, hour=0),      # ежедневно в полночь
    }
}
