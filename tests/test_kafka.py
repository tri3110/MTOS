from kafka import KafkaProducer

producer = KafkaProducer(bootstrap_servers='localhost:9092')

producer.send('test_topic', b'hello kafka')
producer.flush()

print("Sent!")