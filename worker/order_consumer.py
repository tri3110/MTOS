import sys
import os
from apps.payments.services.momo import MomoService

# fix path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# fix settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

import json
from kafka import KafkaConsumer
from apps.orders.models import Order

consumer = KafkaConsumer(
    "order_created",
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda x: json.loads(x.decode('utf-8')),
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id="order_group"
)

print("Worker started...")

for message in consumer:
    data = message.value
    order_id = data["order_id"]

    try:
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            print(f"Order {order_id} not found, skip")
            continue

        if order.status != "PENDING":
            continue

        momo_res = MomoService.create_payment(order)

        order.payment_url = momo_res.get("payUrl")
        order.qr_code = momo_res.get("qrCodeUrl")
        order.status = "WAITING_PAYMENT"
        order.save()

    except Exception as e:
        print("Error:", e)