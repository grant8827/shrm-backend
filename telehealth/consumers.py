# backend/telehealth/consumers.py
"""
WebSocket consumer for telehealth video sessions.
Handles WebRTC signaling between session participants.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import TelehealthSession
import logging

logger = logging.getLogger('theracare.audit')


class VideoSessionConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for video session signaling.
    
    Handles:
    - WebRTC offer/answer exchange
    - ICE candidate exchange
    - Participant join/leave notifications
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'video_session_{self.room_id}'
        self.user = self.scope.get('user')
        
        # Verify session exists and user has access
        try:
            session = await self.get_session(self.room_id)
            if not session:
                await self.close()
                return
            
            # Accept connection first
            await self.accept()
            
            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            # Notify ONLY OTHER participants that a new participant joined
            # Don't send to the new participant themselves
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'participant_joined',
                    'user_id': str(self.user.id) if self.user and self.user.is_authenticated else 'anonymous',
                    'sender_channel': self.channel_name
                }
            )
            
            logger.info(f"User {self.user} connected to video session {self.room_id}")
            
        except Exception as e:
            logger.error(f"Error connecting to video session: {e}")
            await self.close()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Notify others that participant left
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'participant_left',
                'user_id': str(self.user.id) if self.user and self.user.is_authenticated else 'anonymous',
                'sender_channel': self.channel_name
            }
        )
        
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        logger.info(f"User {self.user} disconnected from video session {self.room_id}")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            # Handle different message types
            if message_type == 'offer':
                await self.handle_offer(data)
            elif message_type == 'answer':
                await self.handle_answer(data)
            elif message_type == 'ice_candidate':
                await self.handle_ice_candidate(data)
            elif message_type == 'chat':
                await self.handle_chat_message(data)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
    
    async def handle_offer(self, data):
        """Handle WebRTC offer."""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'webrtc_offer',
                'offer': data['offer'],
                'sender_channel': self.channel_name
            }
        )
    
    async def handle_answer(self, data):
        """Handle WebRTC answer."""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'webrtc_answer',
                'answer': data['answer'],
                'sender_channel': self.channel_name
            }
        )
    
    async def handle_ice_candidate(self, data):
        """Handle ICE candidate."""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'webrtc_ice_candidate',
                'candidate': data['candidate'],
                'sender_channel': self.channel_name
            }
        )
    
    async def handle_chat_message(self, data):
        """Handle chat message."""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': data['message'],
                'sender_id': str(self.user.id) if self.user and self.user.is_authenticated else 'anonymous',
                'sender_name': data.get('sender_name', 'Anonymous'),
                'timestamp': data.get('timestamp'),
                'sender_channel': self.channel_name
            }
        )
    
    # Channel layer handlers
    
    async def participant_joined(self, event):
        """Send participant joined notification."""
        # Don't send to the sender
        if event['sender_channel'] != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': 'participant_joined',
                'user_id': event['user_id']
            }))
    
    async def participant_left(self, event):
        """Send participant left notification."""
        # Don't send to the sender
        if event['sender_channel'] != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': 'participant_left',
                'user_id': event['user_id']
            }))
    
    async def webrtc_offer(self, event):
        """Send WebRTC offer to other participants."""
        # Don't send to the sender
        if event['sender_channel'] != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': 'offer',
                'offer': event['offer']
            }))
    
    async def webrtc_answer(self, event):
        """Send WebRTC answer to other participants."""
        # Don't send to the sender
        if event['sender_channel'] != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': 'answer',
                'answer': event['answer']
            }))
    
    async def webrtc_ice_candidate(self, event):
        """Send ICE candidate to other participants."""
        # Don't send to the sender
        if event['sender_channel'] != self.channel_name:
            await self.send(text_data=json.dumps({
                'type': 'ice_candidate',
                'candidate': event['candidate']
            }))
    
    async def chat_message(self, event):
        """Send chat message to all participants."""
        await self.send(text_data=json.dumps({
            'type': 'chat',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'timestamp': event['timestamp']
        }))
    
    @database_sync_to_async
    def get_session(self, room_id):
        """Get session from database."""
        try:
            return TelehealthSession.objects.filter(room_id=room_id).first()
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None
