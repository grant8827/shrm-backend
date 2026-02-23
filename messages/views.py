from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone
from .models import Message, MessageThread
from .serializers import (
    MessageSerializer,
    MessageThreadSerializer,
    CreateMessageSerializer,
)
from users.models import User
from audit.models import AuditLog
from notifications.models import Notification
import logging
import traceback

logger = logging.getLogger(__name__)


class MessageThreadViewSet(viewsets.ModelViewSet):
    serializer_class = MessageThreadSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return MessageThread.objects.filter(participants=user).distinct()

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        thread = self.get_object()
        Message.objects.filter(thread=thread, is_read=False).exclude(
            sender=request.user
        ).update(is_read=True, read_at=timezone.now())
        return Response({"status": "messages marked as read"})


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        thread_id = self.request.query_params.get("thread_id")

        queryset = Message.objects.filter(thread__participants=user).distinct()

        if thread_id:
            queryset = queryset.filter(thread_id=thread_id)

        return queryset

    def create(self, request):
        try:
            serializer = CreateMessageSerializer(data=request.data)
            if not serializer.is_valid():
                logger.error(f"Validation errors: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            recipient_ids = serializer.validated_data["recipient_ids"]
            content = serializer.validated_data["content"]
            priority = serializer.validated_data.get("priority", "normal")

            logger.info(f"Creating message from {request.user.id} to {recipient_ids}")

            # Get all participants
            recipients = User.objects.filter(id__in=recipient_ids)
            if not recipients.exists():
                logger.error(f"No recipients found for IDs: {recipient_ids}")
                return Response(
                    {"error": "Invalid recipient IDs"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            all_participant_ids = set(
                [str(request.user.id)] + [str(r.id) for r in recipients]
            )
            logger.info(f"Participant IDs: {all_participant_ids}")

            # Find existing thread with same participants
            thread = None
            for existing_thread in MessageThread.objects.filter(
                participants=request.user
            ):
                thread_participant_ids = set(
                    [str(p.id) for p in existing_thread.participants.all()]
                )
                if thread_participant_ids == all_participant_ids:
                    thread = existing_thread
                    logger.info(f"Found existing thread: {thread.id}")
                    break

            # Create new thread if none exists
            if not thread:
                logger.info("Creating new thread")
                # Generate subject from participant names
                recipient_names = [r.get_full_name() or r.username for r in recipients]
                subject = f"Conversation with {', '.join(recipient_names)}"

                thread = MessageThread.objects.create(subject=subject)
                thread.participants.add(request.user)
                for recipient in recipients:
                    thread.participants.add(recipient)
                logger.info(f"Created new thread: {thread.id}")

            # Create message
            logger.info("Creating message object")
            message = Message(thread=thread, sender=request.user, priority=priority)
            logger.info(f"Setting content: {content[:50]}...")
            message.content = content  # Use property setter for encryption
            logger.info("Saving message")
            message.save()
            logger.info(f"Message saved: {message.id}")

            # Create notifications for recipients
            try:
                for recipient in recipients:
                    Notification.objects.create(
                        user=recipient,
                        notification_type="message",
                        title="New Message",
                        message="You have a new message",
                        related_object_id=message.id,
                    )
                logger.info(f"Created notifications for {len(recipients)} recipients")
            except Exception as notif_error:
                logger.warning(f"Failed to create notifications: {str(notif_error)}")
                # Continue even if notification creation fails

            # Log audit
            try:
                AuditLog.objects.create(
                    user=request.user,
                    action="MESSAGE_SENT",
                    resource="message",
                    resource_id=str(message.id),
                )
                logger.info("Audit log created")
            except Exception as audit_error:
                logger.warning(f"Failed to create audit log: {str(audit_error)}")
                # Continue even if audit logging fails

            serialized_data = MessageSerializer(message).data
            logger.info("Returning response")
            return Response(serialized_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error creating message: {str(e)}")
            logger.error(traceback.format_exc())
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=["post"])
    def toggle_star(self, request, pk=None):
        message = self.get_object()
        message.is_starred = not message.is_starred
        message.save()
        return Response({"is_starred": message.is_starred})

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        message = self.get_object()
        if message.sender != request.user:
            message.is_read = True
            message.read_at = timezone.now()
            message.save()
        return Response({"status": "marked as read"})
