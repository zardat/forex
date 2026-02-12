import os
from celery import Celery 

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# making the app visible to celery
app = Celery('core')

app.config_from_object("django.conf:settings", namespace='CELERY')

# fetches task made for celery
app.autodiscover_tasks()