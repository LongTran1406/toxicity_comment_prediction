from fastapi import FastAPI, HTTPException
import mlflow.sklearn
import pandas as pd
import os, mlflow, json, time, uuid
from datetime import datetime
from kafka import KafkaProducer
from prometheus_client import Counter, Histogram, make_asgi_app
import redis

app = FastAPI(title="Toxicity Prediction API")
app.mount("/metrics", make_asgi_app())

REQUEST_COUNTER = Counter("api_requests_total", "Total requests")
REQUEST_LATENCY = Histogram("request_latency", "Prediction latency (seconds)")

mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000"))
model = mlflow.sklearn.load_model("models:/MultinomialNB/Production")

r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, decode_responses=True)

producer = KafkaProducer(
    bootstrap_servers=[os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")],
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

RATE_LIMIT = 10   # requests
RATE_WINDOW = 60  # seconds


def check_rate_limit(user_id: str):
    key = f"ratelimit:{user_id}"
    count = r.incr(key)
    if count == 1:
        r.expire(key, RATE_WINDOW)
    if count > RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")


@app.post("/predict")
def predict(user_id: str, message: str):
    check_rate_limit(user_id)

    REQUEST_COUNTER.inc()
    start = time.time()

    input_series = pd.Series([message])
    prediction = model.predict(input_series)[0]
    probability = model.predict_proba(input_series)[0][1]
    latency = time.time() - start

    REQUEST_LATENCY.observe(latency)

    # Send to Kafka for monitoring / drift detection
    producer.send("model_predictions", value={
        "comment_id": str(uuid.uuid4())[:8],
        "user_id": user_id,
        "message": message,
        "prediction": int(prediction),
        "probability": float(probability),
        "latency": latency,
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    producer.flush()

    return {
        "toxicity_label": int(prediction),
        "toxicity_probability": float(probability)
    }