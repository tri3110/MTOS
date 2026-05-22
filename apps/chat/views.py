from django.db.models import (
    Count,
    OuterRef,
    Subquery,
    IntegerField,
)
from django.db.models.functions import Coalesce
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction

from apps.chat.models import (
    ConversationParticipant,
    Message,
)
from apps.chat.models.conversation import Conversation
from apps.chat.service import create_chat_message
from apps.users.models import User
from apps.websocket.service import broadcast_message, send_conversation_update, send_notification
from common.constants import UserCache
from common.redis_client import redis_client

class ConversationListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = request.user

        unread_subquery = (
            Message.objects.filter(
                conversation_id=OuterRef("conversation_id"),
                id__gt=Coalesce(
                    OuterRef("last_read_message_id"),
                    0
                )
            )
            .values("conversation_id")
            .annotate(total=Count("id"))
            .values("total")[:1]
        )

        participants = (
            ConversationParticipant.objects
            .filter(user=user)
            .select_related(
                "conversation",
                "conversation__last_message",
            )
            .prefetch_related(
                "conversation__participants__user"
            )
            .annotate(
                unread_count=Coalesce(
                    Subquery(
                        unread_subquery,
                        output_field=IntegerField()
                    ),
                    0
                )
            )
            .order_by(
                "-conversation__last_message_at"
            )
        )

        results = []

        for participant in participants:

            conversation = participant.conversation
            last_message = conversation.last_message

            conversation_name = conversation.name
            conversation_avatar = conversation.avatar
            is_online = False

            if conversation.type == "private":

                other_participant = next(
                    (
                        p for p in conversation.participants.all()
                        if p.user_id != user.id
                    ),
                    None
                )

                if other_participant:
                    conversation_name = (
                        other_participant.user.full_name
                        or other_participant.user.username
                    )

                    conversation_avatar = getattr(
                        other_participant.user,
                        "avatar",
                        None
                    )

                is_online = bool(redis_client.get(UserCache.ONLINE.key + f":{other_participant.user_id}")) if other_participant else False

            group_users = []
            if conversation.type == "group":

                group_users = [
                    {
                        "user_id": p.user.id,
                        "role": p.role,
                        "name": (
                            p.user.full_name
                            or p.user.username
                        ),
                        "is_online": bool(redis_client.get(UserCache.ONLINE.key + f":{p.user.id}")),
                        "avatar": getattr(
                            p.user,
                            "avatar",
                            None
                        )
                    }

                    for p in conversation.participants.all()
                ]

            results.append({
                "conversation_id": conversation.id,
                "conversation_type": conversation.type,
                "conversation_name": conversation_name,
                "avatar": conversation_avatar,
                "unread_count": participant.unread_count,
                "group_users": group_users,
                "is_online": is_online,
                "last_message": {
                    "id": last_message.id if last_message else None,
                    "content": (
                        last_message.content
                        if last_message else None
                    ),
                    "sender_id": (
                        last_message.sender_id
                        if last_message else None
                    ),
                    "created_at": (
                        last_message.created_at.isoformat()
                        if last_message else None
                    )
                },
                "last_message_at": (
                    conversation.last_message_at.isoformat()
                    if conversation.last_message_at else None
                )
            })

        return Response(results)


class ConversationCreateAPIView(APIView):

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        try:

            current_user = request.user
            user_id = request.data.get("user_id")

            if not user_id:
                return Response(
                    {
                        "message": "user_id is required"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            if int(user_id) == current_user.id:
                return Response(
                    {
                        "message": "Cannot create conversation with yourself"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                target_user = User.objects.get(id=user_id)

            except User.DoesNotExist:
                return Response(
                    {
                        "message": "User not found"
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            # find existing private conversation
            existing_conversation = (
                Conversation.objects
                .filter(type="private")
                .filter(
                    participants__user=current_user
                )
                .filter(
                    participants__user=target_user
                )
                .distinct()
                .first()
            )

            if existing_conversation:

                return Response({
                    "conversation_id": existing_conversation.id,
                    "conversation_type": existing_conversation.type,
                    "conversation_name": (
                        target_user.full_name
                        or target_user.username
                    ),
                    "avatar": getattr(
                        target_user,
                        "avatar",
                        None
                    )
                })

            # create new conversation
            conversation = Conversation.objects.create(
                type="private"
            )

            ConversationParticipant.objects.bulk_create([
                ConversationParticipant(
                    conversation=conversation,
                    user=current_user,
                    role="member"
                ),

                ConversationParticipant(
                    conversation=conversation,
                    user=target_user,
                    role="member"
                )
            ])

            response_data = {
                "conversation_id": conversation.id,
                "conversation_type": conversation.type,
                "conversation_name": (
                    target_user.full_name
                    or target_user.username
                ),
                "avatar": getattr(
                    target_user,
                    "avatar",
                    None
                ),
                "unread_count": 0,
                "group_users": [],
                "is_online": False,
                "last_message": None,
                "last_message_at": None,
            }

            return Response(
                response_data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            print("Error creating conversation:", str(e))
            return Response(
                {
                    "message": "An error occurred while creating conversation."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ConversationMessageListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_id):

        user = request.user

        # validate user belongs to room
        is_participant = ConversationParticipant.objects.filter(
            conversation_id=conversation_id,
            user=user
        ).exists()

        if not is_participant:
            return Response(
                {
                    "detail": "Conversation not found."
                },
                status=404
            )

        messages = (
            Message.objects
            .filter(
                conversation_id=conversation_id,
                is_deleted=False
            )
            .select_related("sender")
            .order_by("id")
        )

        results = []

        for message in messages:

            results.append({
                "id": message.id,
                "sender": (
                    "admin"
                    if message.sender_id == user.id
                    else "remote"
                ),
                "sender_id": message.sender_id,
                "sender_name": (
                    message.sender.full_name
                    or message.sender.username
                ),
                "message_type": message.type,
                "text": message.content,
                "timestamp": (
                    message.created_at.isoformat()
                ),
                "is_edited": message.is_edited,
            })

        # update read pointer
        latest_message = messages.last()

        if latest_message:

            ConversationParticipant.objects.filter(
                conversation_id=conversation_id,
                user=user
            ).update(
                last_read_message=latest_message
            )

        return Response(results)
      
    
class SendMessageAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, conversation_id):

        try:

            user = request.user

            content = request.data.get("content")

            if not content:
                return Response(
                    {
                        "detail": "Content is required."
                    },
                    status=400
                )

            is_participant = ConversationParticipant.objects.filter(
                conversation_id=conversation_id,
                user=user
            ).exists()

            if not is_participant:
                return Response(
                    {
                        "detail": "Conversation not found."
                    },
                    status=404
                )

            message = create_chat_message(
                conversation_id=conversation_id,
                sender=user,
                content=content
            )

            participants = ConversationParticipant.objects.filter(
                conversation_id=conversation_id
            ).exclude(
                user=user
            ).select_related("user")

            message_data = {
                "id": message.id,
                "conversation_id": conversation_id,
                "sender_id": user.id,
                "sender_name": user.full_name or user.username,
                "message_type": message.type,
                "text": message.content,
                "timestamp": message.created_at.isoformat(),
                "is_edited": message.is_edited,
            }

            for participant in participants:
                send_notification(
                    participant.user.id,
                    "New message",
                    f"{user.full_name or user.username}: {content}"
                )
                send_conversation_update(
                    participant.user.id,
                    {
                        "conversation_id": conversation_id,
                        "message": message_data
                    }
                )

            broadcast_message(
                room_id=conversation_id,
                data=message_data
            )

            return Response(message_data)
        
        except Exception as e:
            print("Error sending message:", str(e))
            return Response(
                {
                    "detail": "Conversation not found."
                },
                status=404
            )
        
class GroupUserAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, conversation_id):

        user = request.user
        user_id = request.data.get("user_id")

        if not user_id:
            return Response(
                {
                    "detail": "user_id is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:

            participant = ConversationParticipant.objects.select_related(
                "conversation"
            ).get(
                conversation_id=conversation_id,
                user=user
            )

        except ConversationParticipant.DoesNotExist:

            return Response(
                {
                    "detail": "Conversation not found."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        conversation = participant.conversation

        # only group
        if conversation.type != "group":
            return Response(
                {
                    "detail": "Only group conversations support removing users."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # permission
        if participant.role not in ["owner", "admin"]:
            return Response(
                {
                    "detail": "Permission denied."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        try:

            target_participant = ConversationParticipant.objects.select_related(
                "user"
            ).get(
                conversation_id=conversation_id,
                user_id=user_id
            )

        except ConversationParticipant.DoesNotExist:

            return Response(
                {
                    "detail": "User not found in group."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # cannot remove owner
        if target_participant.role == "owner":
            return Response(
                {
                    "detail": "Cannot remove owner."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # admin cannot remove another admin
        if (
            participant.role == "admin"
            and target_participant.role == "admin"
        ):
            return Response(
                {
                    "detail": "Admin cannot remove another admin."
                },
                status=status.HTTP_403_FORBIDDEN
            )

        removed_user = target_participant.user

        target_participant.delete()

        # websocket broadcast
        broadcast_message(
            room_id=conversation_id,
            data={
                "type": "group_user_removed",
                "conversation_id": conversation_id,
                "user_id": removed_user.id,
            }
        )

        # notify removed user
        send_notification(
            removed_user.id,
            "Removed from group",
            f"You were removed from {conversation.name}"
        )

        send_conversation_update(
            removed_user.id,
            {
                "type": "conversation_removed",
                "conversation_id": conversation_id,
            }
        )

        return Response({
            "success": True,
            "removed_user_id": removed_user.id
        })