# Celery Tasks Module
from celery import Celery
from config import Config

# Initialize Celery
celery_app = Celery('tasks')
celery_app.config_from_object(Config)

# Auto-discover tasks
celery_app.autodiscover_tasks(['tasks'])

# Example task
@celery_app.task
def test_task():
    """Test task"""
    return 'Task completed successfully'
