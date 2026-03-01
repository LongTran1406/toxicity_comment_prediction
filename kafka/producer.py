from kafka import KafkaProducer
import json

producer = KafkaProducer(bootstrap_servers=['kafka:9092'], value_serializer=lambda v: json.dumps(v).encode("utf-8"))

for i in range (200, 300):
    event = {
        "id": i,
        "message": f'Hello {i}'
    }
    producer.send(topic='raw_data', value=event)

    #  ensure all messages are sent before the script exits
    producer.flush()

