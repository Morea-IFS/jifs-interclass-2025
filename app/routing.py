# routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/scoreboard/$', consumers.ScoreboardConsumer.as_asgi()),
    re_path(r'ws/public/$', consumers.PublicConsumer.as_asgi()),
    re_path(r'ws/admin/$', consumers.AdminConsumer.as_asgi()),
]
