from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def send_order_created(order):
    producer.send("order_created", {
        "order_id": order.id,
        "user_id": order.user.id,
        "total": str(order.total_price)
    })
    producer.flush()