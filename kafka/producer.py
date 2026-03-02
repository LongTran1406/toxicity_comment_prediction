from kafka import KafkaProducer
import json
from datetime import datetime
import time

producer = KafkaProducer(bootstrap_servers=['kafka:9092'], value_serializer=lambda v: json.dumps(v).encode("utf-8"))

for i in range(200, 300):
    event = {
        "id": i,
        "user_id": f"user_{i % 5}", 
        "message": f'Hello {i}',
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
    }
    producer.send(topic='raw_data', value=event)
    print(f"Sent: {event}")
    time.sleep(1)

producer.flush()
