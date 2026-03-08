# Sentinex: Sentiment Classifier ML System

## Introduction
A production-grade machine learning system for real-time toxicity comment prediction. The system ingests comments via a REST API, processes them through a real-time feature pipeline, and returns toxicity predictions using a trained classifier registered in MLflow.

- **Real-time prediction** — sub-second toxicity scoring via REST API
- **Streaming feature pipeline** — Kafka → Flink → Redis for online feature serving
- **Batch data pipeline** — Airflow + Spark for bronze → silver → gold data transformation
- **Experiment tracking** — MLflow for model versioning and registry
- **Cloud-native serving** — FastAPI deployed on AKS with auto-scaling
- **Observability** — Prometheus + Grafana for API and infrastructure monitoring
- **CI/CD** — GitHub Actions for automated build, push to ACR, and deploy to AKS

## Overall System Architecture
<div style="text-align: center;"> <img src="images\System_Diagram.jpg" style="width: 1188px; height: auto;"></div>


# Table of Contents
- [Introduction](#introduction)
- [Overall System Architecture](#overall-system-architecture)
- [Project Structure](#project-structure)
- [Local](#local)
  - [Demo](#demo)
  - [Running in Docker Compose](#running-in-docker-compose)
  - [Local K8S Setup](#local-k8s-setup)
- [Cloud](#cloud)
  - [Deploying to Azure](#deploying-to-azure)

## Project Structure
```txt
├── .github
│   └── workflows
│       ├── airflow.yml
│       └── fastapi.yml
├── airflow
│   ├── Dockerfile
│   ├── dags
│   │   ├── batch_processing.py
│   │   ├── ingest_data_to_minio.py
│   │   ├── silver_data_validation.py
│   │   └── silver_to_gold.py
│   ├── docker-compose.yml
│   ├── hive
│   ├── minio
│   │   └── data
│   ├── postgres
│   ├── spark
│   │   └── scripts
│   │       ├── batch_processing.py
│   │       ├── data_validation.py
│   │       └── gold_transform.py
│   └── trino
│       └── etc
│           └── catalog
├── data
├── flink
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── streaming_to_gold.py
├── k8s
│   ├── 00-secrets.yaml
│   ├── 01-fastapi-local.yaml
│   └── 01-fastapi.yaml
├── kafka
│   ├── consumer.py
│   ├── docker-compose.yml
│   └── producer.py
├── ml
│   ├── Dockerfile
│   ├── data_cleaning.py
│   ├── docker-compose.yml
│   ├── inference_test.py
│   ├── main.py
│   ├── text_processor.py
│   └── train.py
├── monitoring
│   ├── docker-compose.yml
│   └── prometheus.yml
├── serving
    └── fastapi
        ├── Dockerfile
        ├── app.py
        ├── docker-compose.yml
        ├── feature_store.py
        └── text_processor.py
```

# Local
## Demo

### Running in docker-compos
####  Start all services 
```bash
# Start data platform (Airflow, Spark, MinIO, Hive, Trino)
cd airflow && docker compose up -d

# Start Kafka
cd kafka && docker compose up -d

# Start Flink feature store
cd flink && docker compose up -d

# Start MLflow
cd ml && docker compose up -d

# Start monitoring
cd monitoring && docker compose up -d
```

#### Train and register the model
```bash
cd ml
docker "container_name" exec -it python main.py
```
This trains the model and registers it to MLflow. Then promote it to Production

```bash
curl -X POST http://localhost:5000/api/2.0/mlflow/model-versions/transition-stage \
  -H "Content-Type: application/json" \
  -d '{"name": "MultinomialNB", "version": "1", "stage": "Production"}'
```

#### Start FastAPI
```bash
cd serving/fastapi
docker compose up -d
```

#### Test API
```bash
curl -X POST "http://localhost:8000/predict?user_id=user123&message=you+are+so+handsome"
```
#### Example output
```bash
{"comment_id":"f4b94a62","toxicity_label":0,"toxicity_probability":0.339546749165074}
```

### Local K8S setup
#### Point to minikube docker
```bash
minikube -p minikube docker-env --shell powershell | Invoke-Expression
```

#### Build image
```bash
cd serving/fastapi
docker build -t fastapi-custom:latest .
```

#### Deploy
```bash
kubectl apply -f k8s/00-secrets.yaml
kubectl apply -f k8s/01-fastapi.yaml
```

#### See running pod status (optional)
```bash
minikube service fastapi -n data-platform
```

#### Rollout the update
```bash
kubectl rollout restart deployment/fastapi -n data-platform
```

#### Export the port 
```bash
kubectl port-forward svc/fastapi 8000:8000 -n data-platform
```

#### Send request
```bash
Invoke-WebRequest -Method POST "http://localhost:8000/predict?user_id=testuser1&message=you+are+so+stupid+and+ugly" -UseBasicParsing | Select-Object -ExpandProperty Content
```

# Cloud
## Deploying to Azure

### Create AKS cluster and ACR
```bash
az group create --name data-platform-rg --location southeastasia

az acr create --resource-group data-platform-rg \
  --name toxicityregistry2026 --sku Basic

az aks create --resource-group data-platform-rg \
  --name data-platform-cluster \
  --attach-acr toxicityregistry2026
```

### Create namespace and secrets
```bash
kubectl create namespace data-platform

kubectl create secret generic fastapi-secrets \
  --from-literal=AWS_ACCESS_KEY_ID=<minio-access-key> \
  --from-literal=AWS_SECRET_ACCESS_KEY=<minio-secret-key> \
  -n data-platform
```

### Build and push image to ACR
```bash
az acr build --registry toxicityregistry2026 \
  --image fastapi-custom:latest serving/fastapi/
```

### Deploy to AKS
```bash
kubectl apply -f k8s/00-secrets.yaml
kubectl apply -f k8s/01-fastapi.yaml
```

### Get external IP
```bash
kubectl get service fastapi -n data-platform
```

### Test the API
```bash
curl -X POST "http://<EXTERNAL-IP>:8000/predict?user_id=user123&message=you+are+so+stupid"
```
