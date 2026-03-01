import json
from kafka import KafkaConsumer

consumer = KafkaConsumer(
    'raw_data',
    bootstrap_servers=['kafka:9092'],
    value_deserializer=lambda v: json.loads(v.decode('utf-8')),
    auto_offset_reset='earliest'
)

for message in consumer:
    print(message.value)