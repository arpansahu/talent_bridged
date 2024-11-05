from django.urls import re_path
from celery_progress_custom_app.consumers import ProgressConsumer

websocket_urlpatterns = [
    re_path(r'ws/progress/(?P<task_id>[0-9a-f-]+)/$', ProgressConsumer.as_asgi()),
]
