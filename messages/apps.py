from django.apps import AppConfig


class MessagesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "messages"
    label = "theracare_messages"  # Unique label to avoid conflict with django.contrib.messages
    verbose_name = "Secure Messaging"
