import json
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers=["localhost:9092"],
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),

    # batching (tăng performance)
    linger_ms=5,
    batch_size=16384,

    # reliability
    acks="all",
    retries=10,

    # compression
    compression_type="gzip"
)

def publish_event(data):
    try:
        producer.send("cart-topic", value=data)
        producer.flush()  # đảm bảo gửi ngay (dev), prod có thể bỏ

    except Exception as e:
        print("Kafka error:", e)