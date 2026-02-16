import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

class VideoCallConsumer(AsyncWebsocketConsumer):
    # Class-level dict to track participants per room
    room_participants = {}
    
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'video_call_{self.session_id}'

        # Track participant count
        if self.room_group_name not in VideoCallConsumer.room_participants:
            VideoCallConsumer.room_participants[self.room_group_name] = set()
        
        # Add this connection to the room
        VideoCallConsumer.room_participants[self.room_group_name].add(self.channel_name)

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        
        print(f"[WS] Participant connected to {self.room_group_name}, total: {len(VideoCallConsumer.room_participants[self.room_group_name])}")

    async def disconnect(self, close_code):
        # Remove from participant tracking
        if self.room_group_name in VideoCallConsumer.room_participants:
            VideoCallConsumer.room_participants[self.room_group_name].discard(self.channel_name)
            if len(VideoCallConsumer.room_participants[self.room_group_name]) == 0:
                del VideoCallConsumer.room_participants[self.room_group_name]
        
        print(f"[WS] Participant disconnected from {self.room_group_name}")
        
        # Notify others that participant left
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'participant_left',
                'channel_name': self.channel_name
            }
        )
        
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        print(f"[WS] Received message type: {message_type}")
        
        # Handle participant joined notification
        if message_type == 'participant_joined':
            # Notify all OTHER participants that someone joined
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
            # Forward all other signaling messages (offer, answer, ice_candidate)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'video_message',
                    'message': data,
                    'sender_channel': self.channel_name
                }
            )

    async def participant_joined_broadcast(self, event):
        # Don't send to the sender (the person who just joined)
        if event['sender_channel'] != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': 'participant_joined',
                'user_id': event['user_id'],
                'user_name': event['user_name']
            }))
            print(f"[WS] Notified existing participant about new joiner")

    async def participant_left(self, event):
        # Don't send to the sender (the person who left)
        if event['channel_name'] != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': 'participant_left'
            }))
            print(f"[WS] Notified participant about someone leaving")

    async def video_message(self, event):
        # Don't send to the sender
        if event['sender_channel'] != self.channel_name:
            await self.send(text_data=json.dumps(event['message']))
            print(f"[WS] Forwarded {event['message'].get('type')} to peer")