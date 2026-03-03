FROM ghcr.io/mlflow/mlflow:latest

USER root
RUN apt-get update && apt-get install -y default-jdk && apt-get clean

COPY requirements.txt .
RUN pip install -r requirements.txt