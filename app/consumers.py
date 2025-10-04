# app/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings

class ScoreboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if settings.DEBUG: print("Websocket da rota scoreboard funcionando.")
        await self.channel_layer.group_add("scoreboard", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if settings.DEBUG: print("Websocket da rota scoreboard desconectado.")
        await self.channel_layer.group_discard("scoreboard", self.channel_name)


    async def time_new(self, event):
        if settings.DEBUG: print("Canal de comunicação do scoreboard: time.")
        match_data = event['match']
        await self.send(text_data=json.dumps({
            "type": "time",
            "data": match_data
        }))

    async def penalties_new(self, event):
        if settings.DEBUG: print("Canal de comunicação do scoreboard: penalidades.")
        match_data = event['match']
        await self.send(text_data=json.dumps({
            "type": "penalties",
            "data": match_data
        }))

    async def point_new(self, event):
        if settings.DEBUG: print("Canal de comunicação do scoreboard: point.")
        match_data = event['match']
        await self.send(text_data=json.dumps({
            "type": "point",
            "data": match_data
        }))

    async def match_new(self, event):
        if settings.DEBUG: print("Canal de comunicação do scoreboard: match")
        match_data = event['match']
        await self.send(text_data=json.dumps({
            "type": "match",
            "data": match_data
        }))

    async def banner_new(self, event):
        if settings.DEBUG: print("Canal de comunicação do scoreboard: banner")
        match_data = event['match']
        await self.send(text_data=json.dumps({
            "type": "banner",
            "data": match_data
        }))

class PublicConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("public", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("public", self.channel_name)

    async def time_new(self, event):
        if settings.DEBUG: print("Canal de comunicação do scoreboard: time.")
        match_public = event['match']
        await self.send(text_data=json.dumps({
            "type": "time",
            "data": match_public
        }))

    async def penalties_new(self, event):
        if settings.DEBUG: print("Canal de comunicação do scoreboard: penalidades.")
        match_public = event['match']
        await self.send(text_data=json.dumps({
            "type": "penalties",
            "data": match_public
        }))

    async def point_new(self, event):
        if settings.DEBUG: print("Canal de comunicação do public: point.")
        match_public = event['match']
        await self.send(text_data=json.dumps({
            "type": "point",
            "data": match_public
        }))

    async def match_new(self, event):
        if settings.DEBUG: print("Canal de comunicação do public: match")
        match_public = event['match']
        await self.send(text_data=json.dumps({
            "type": "match",
            "data": match_public
        }))

class AdminConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("admin", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("admin", self.channel_name)

    async def match_update(self, event):
        if settings.DEBUG: print("Canal de comunicação: admin.")
        match_data = event['match']
        await self.send(text_data=json.dumps(match_data))