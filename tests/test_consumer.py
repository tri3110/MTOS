from kafka import KafkaConsumer

consumer = KafkaConsumer(
    'test_topic',
    bootstrap_servers='localhost:9092'
)

print("Waiting for message...")

for message in consumer:
    print("Received:", message.value)