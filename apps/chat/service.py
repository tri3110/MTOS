from channels.db import database_sync_to_async
from django.db import transaction
from apps.chat.models import (
    Conversation,
    ConversationParticipant,
    Message,
)

def create_chat_message(
    conversation_id,
    sender,
    content,
):

    with transaction.atomic():

        conversation = Conversation.objects.select_for_update().get(
            id=conversation_id
        )

        message = Message.objects.create(
            conversation=conversation,
            sender=sender,
            type=Message.MessageType.TEXT,
            content=content,
        )

        conversation.last_message = message
        conversation.last_message_at = message.created_at

        conversation.save(
            update_fields=[
                "last_message",
                "last_message_at",
            ]
        )

        ConversationParticipant.objects.filter(
            conversation_id=conversation_id,
            user=sender
        ).update(
            last_read_message=message
        )

    return message

@database_sync_to_async
def mark_message_read(
    user,
    room_id,
    message_id,
):

    try:

        message = Message.objects.get(
            id=message_id,
            conversation_id=room_id
        )

        participant = ConversationParticipant.objects.get(
            conversation_id=room_id,
            user=user
        )

        current_last_read_id = (
            participant.last_read_message_id or 0
        )

        if message.id <= current_last_read_id:
            return

        participant.last_read_message = message

        participant.save(
            update_fields=[
                "last_read_message"
            ]
        )

    except (
        Message.DoesNotExist,
        ConversationParticipant.DoesNotExist,
    ):
        return
    
@database_sync_to_async
def get_user_conversations(user_id):

    return list(
        ConversationParticipant.objects.filter(
            user_id=user_id
        ).values_list(
            "conversation_id",
            flat=True
        )
    )