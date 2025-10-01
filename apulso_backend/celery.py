import os
from celery import Celery

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'apulso_backend.settings')

app = Celery('apulso_backend')

# Load config from Django settings with CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
