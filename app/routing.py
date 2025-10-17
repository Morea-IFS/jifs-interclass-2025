# routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/scoreboard/(?P<event_id>\w+)/$', consumers.ScoreboardConsumer.as_asgi()),
    re_path(r'ws/public/(?P<event_id>\w+)/$', consumers.PublicConsumer.as_asgi()),
    re_path(r'ws/admin/(?P<event_id>\w+)/$', consumers.AdminConsumer.as_asgi()),
]
