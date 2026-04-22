from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import uuid
from datetime import datetime

def send_notification(user_id, title, message, level="info"):
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",
        {
            "type": "notify",
            "payload": {
                "id": str(uuid.uuid4()),
                "title": title,
                "message": message,
                "level": level,
                "created_at": datetime.now().isoformat()
            }
        }
    )

def notify_user(user_id, message, event_type="USER_DELETED"):
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",
        {
            "type": "user_event",
            "data": {
                "type": event_type,
                "message": message
            }
        }
    )