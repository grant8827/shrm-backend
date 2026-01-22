import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

class VideoCallConsumer(AsyncWebsocketConsumer):
    # Class-level dict to track participant count per room
    room_participants = {}
    
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'video_call_{self.session_id}'

        # Track participant count
        if self.room_group_name not in VideoCallConsumer.room_participants:
            VideoCallConsumer.room_participants[self.room_group_name] = 0
        VideoCallConsumer.room_participants[self.room_group_name] += 1

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Decrement participant count
        if self.room_group_name in VideoCallConsumer.room_participants:
            VideoCallConsumer.room_participants[self.room_group_name] -= 1
            if VideoCallConsumer.room_participants[self.room_group_name] <= 0:
                del VideoCallConsumer.room_participants[self.room_group_name]
        
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
        
        # Handle request for participant count
        if data.get('type') == 'request_participant_count':
            count = VideoCallConsumer.room_participants.get(self.room_group_name, 0)
            await self.send(text_data=json.dumps({
                'type': 'participant_count',
                'count': count
            }))
            return
        
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