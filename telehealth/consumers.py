import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

class VideoCallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'video_call_{self.session_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Notify others that participant left
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'participant_left',
                'channel_name': self.channel_name
            }
        )
        
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        
        # Handle participant joined notification
        if data.get('type') == 'participant_joined':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'participant_joined_broadcast',
                    'user_id': data.get('user_id'),
                    'user_name': data.get('user_name'),
                    'sender_channel': self.channel_name
                }
            )
        else:
            # Forward signaling messages to other participants
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'video_message',
                    'message': data,
                    'sender_channel': self.channel_name
                }
            )

    async def participant_joined_broadcast(self, event):
        # Don't send to the sender
        if event['sender_channel'] != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': 'participant_joined',
                'user_id': event['user_id'],
                'user_name': event['user_name']
            }))

    async def participant_left(self, event):
        # Don't send to the sender
        if event['channel_name'] != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': 'participant_left'
            }))

    async def video_message(self, event):
        # Don't send to the sender
        if event['sender_channel'] != self.channel_name:
            await self.send(text_data=json.dumps(event['message']))