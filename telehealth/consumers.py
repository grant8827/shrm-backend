import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache
from asgiref.sync import sync_to_async
from datetime import datetime


class VideoCallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        self.room_group_name = f"video_call_{self.session_id}"
        self.room_participants_key = f"participants_{self.room_group_name}"

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Update participant list in cache
        participants = await sync_to_async(cache.get)(self.room_participants_key, set())
        participants.add(self.channel_name)
        await sync_to_async(cache.set)(
            self.room_participants_key, participants, timeout=86400  # 24h timeout
        )

        print(
            f"[WS] Participant connected to {self.room_group_name}, "
            f"total: {len(participants)}"
        )

    async def disconnect(self, close_code):
        # Notify others that participant left
        await self.channel_layer.group_send(
            self.room_group_name,
            {"type": "participant_left", "channel_name": self.channel_name},
        )

        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        # Remove from participant tracking
        participants = await sync_to_async(cache.get)(self.room_participants_key, set())
        if self.channel_name in participants:
            participants.discard(self.channel_name)
            if len(participants) == 0:
                await sync_to_async(cache.delete)(self.room_participants_key)
            else:
                await sync_to_async(cache.set)(
                    self.room_participants_key, participants, timeout=86400
                )

        print(f"[WS] Participant disconnected from {self.room_group_name}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get("type")

        print(f"[WS] Received message type: {message_type}")

        # Add server-side timestamp
        data['timestamp'] = datetime.now().isoformat()

        # Handle participant joined notification
        if message_type == "participant_joined":
            # Notify all OTHER participants that someone joined
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "participant_joined_broadcast",
                    "user_id": data.get("user_id"),
                    "user_name": data.get("user_name"),
                    "sender_channel": self.channel_name,
                },
            )
        else:
            # Forward all other signaling messages (offer, answer, ice_candidate)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "video_message",
                    "message": data,
                    "sender_channel": self.channel_name,
                },
            )

    async def participant_joined_broadcast(self, event):
        # Don't send to the sender (the person who just joined)
        if event["sender_channel"] != self.channel_name:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "participant_joined",
                        "user_id": event["user_id"],
                        "user_name": event["user_name"],
                    }
                )
            )
            print(f"[WS] Notified existing participant about new joiner")

    async def participant_left(self, event):
        # Don't send to the sender (the person who left)
        if event["channel_name"] != self.channel_name:
            await self.send(text_data=json.dumps({"type": "participant_left"}))
            print(f"[WS] Notified participant about someone leaving")

    async def video_message(self, event):
        # Don't send to the sender
        if event["sender_channel"] != self.channel_name:
            await self.send(text_data=json.dumps(event["message"]))
            print(f"[WS] Forwarded {event['message'].get('type')} to peer")
