from kafka import KafkaProducer
import json
from datetime import datetime
import time

producer = KafkaProducer(bootstrap_servers=['kafka:9092'], value_serializer=lambda v: json.dumps(v).encode("utf-8"))

for i in range(200, 300):
    event = {
        "id": i,
        "user_id": f"user_{i % 5}", 
        "message": f'As a local person I can say this and be honest that is it local culture that has gotten us to where we are with hpd and local culture is not going to get us out of this mess.  I feel the same way about how the DOE is looking at mainland candidates. Unfortunately hpd is known around the nation for one thing.  Sex with prostitutes for investigative purposes.  How embarrassing that the good job that so many officers perform every day gets overshadowed by scandal after scandal. It will be a learning process for someone from the mainland so they will need to open to learning and we will have to teach them about Hawaii. But we also need to be open to be taught as we might learn some better ways to run things and clean things up.',
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
    }
    producer.send(topic='raw_data', value=event)
    print(f"Sent: {event}")
    time.sleep(1)

producer.flush()
