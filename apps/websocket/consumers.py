from channels.generic.websocket import AsyncWebsocketConsumer
from apps.chat.service import get_user_conversations
from common.constants import UserCache
from common.redis_client import redis_client
import json

class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        self.user = self.scope["user"]

        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]

        self.room_group_name = f"room_{self.room_id}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        print(f"CONNECTED: {self.channel_name}")

    async def disconnect(self, close_code):

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        print(f"DISCONNECTED: {self.channel_name}")

    async def chat_message(self, event):

        await self.send(text_data=json.dumps({
            "type": "chat_message",
            "data": event["data"]
        }))

class UserConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user_id = self.scope["url_route"]["kwargs"]["user_id"]
        self.group_name = f"user_{self.user_id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        redis_client.set(UserCache.ONLINE.key + f":{self.user_id}", UserCache.ONLINE.ttl)

        self.presence_groups = []

        conversation_ids = await get_user_conversations(self.user_id)

        for conversation_id in conversation_ids:

            group_name = f"presence_{conversation_id}"

            self.presence_groups.append(group_name)

            await self.channel_layer.group_add(
                group_name,
                self.channel_name
            )


        # broadcast online
        for group_name in self.presence_groups:

            await self.channel_layer.group_send(
                group_name,
                {
                    "type": "user_status",
                    "data": {
                        "user_id": int(self.user_id),
                        "is_online": True
                    }
                }
            )

        await self.accept()

    async def disconnect(self, close_code):

        redis_client.delete(UserCache.ONLINE.key + f":{self.user_id}")

        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

        for group_name in self.presence_groups:
            await self.channel_layer.group_send(
                group_name,
                {
                    "type": "user_status",
                    "data": {
                        "user_id": int(self.user_id),
                        "is_online": False
                    }
                }
            )

            await self.channel_layer.group_discard(
                group_name,
                self.channel_name
        )

    async def user_event(self, event):
        await self.send(text_data=json.dumps(event["data"]))

    async def notify(self, event):
        await self.send(text_data=json.dumps({
            "type": "notification",
            "payload": event["payload"]
    }))
        
    async def conversation_update(self, event):
        await self.send(text_data=json.dumps({
            "type": "conversation_update",
            "data": event["data"]
        }))

    async def user_status(self, event):
        await self.send(text_data=json.dumps({
            "type": "user_status",
            "data": event["data"]
        }))