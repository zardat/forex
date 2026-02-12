from .celery import app as celery_app

# django loads celery on startup so celery can discover tasks defined in the project
__all__ = ('celery_app',)