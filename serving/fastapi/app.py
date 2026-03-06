from fastapi import FastAPI
import mlflow.sklearn
import pandas as pd
from feature_store import get_features
import os
import mlflow
from kafka import KafkaProducer
import json
from datetime import datetime
import time
import uuid
from prometheus_client import Counter, Histogram, make_asgi_app

app = FastAPI(title="Toxicity Prediction API")
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


REQUEST_COUNTER = Counter(
    "api_requests_total",
    "The number of requests to the fastapi",
)

REQUEST_LATENCY = Histogram(
    "request_latency",
    "Latency of prediction (seconds)"
)

mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000"))
model = mlflow.sklearn.load_model("models:/MultinomialNB/Production")

producer = KafkaProducer(
    bootstrap_servers=[os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")],
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)


@app.post("/predict")
def predict(user_id: str, message: str, max_wait: int = 10):

    REQUEST_COUNTER.inc()
    start = time.time()

    # 1. Auto-generate comment_id
    comment_id = str(uuid.uuid4())[:8]  # short unique id

    # 2. Send to Kafka
    event = {
        "id": comment_id,
        "user_id": user_id,
        "message": message,
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    producer.send(topic="raw_data", value=event)
    producer.flush()

    # 3. Wait for Flink to process and write to Redis
    features = None
    for _ in range(max_wait * 20):
        features = get_features(comment_id)
        if features is not None:
            break
        time.sleep(0.05)

    if features is None:
        return {"error": f"comment not processed after {max_wait}s"}

    # 4. Predict
    input_series = pd.Series([features["comment_text"]])
    prediction = model.predict(input_series)[0]
    probability = model.predict_proba(input_series)[0][1]

    REQUEST_LATENCY.observe(
        time.time() - start
    )

    return {
        "comment_id": comment_id,
        "toxicity_label": int(prediction),
        "toxicity_probability": float(probability)
    }
