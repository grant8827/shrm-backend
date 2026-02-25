import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class VideoCallConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for WebRTC signaling.
    Relays SDP offers/answers and ICE candidates between participants.
    """

    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group_name = f'video_{self.session_id}'

        # Join room group in Redis
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        
        logger.info(f'WebSocket connected: {self.channel_name} joined room {self.room_group_name}')

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        logger.info(f'WebSocket disconnected: {self.channel_name} left room {self.room_group_name}')

    async def receive(self, text_data):
        """
        Receive message from WebSocket (from React app).
        Broadcast to OTHER participants in the room via Redis.
        """
        try:
            data = json.loads(text_data)
            
            # Broadcast the message to the Redis group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'signal_message',
                    'message': data,
                    'sender_channel_name': self.channel_name  # Track who sent it
                }
            )
            
        except json.JSONDecodeError as e:
            logger.error(f'Invalid JSON received: {e}')
        except Exception as e:
            logger.error(f'Error in receive: {e}')

    async def signal_message(self, event):
        """
        Receive message from Redis group.
        DO NOT send back to the sender - only to other participants.
        """
        # Only send to OTHER participants (not the sender)
        if self.channel_name != event['sender_channel_name']:
            await self.send(text_data=json.dumps(event['message']))
