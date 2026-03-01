FROM apache/airflow:2.11.1

USER root
RUN apt-get update && apt-get install -y default-jdk && apt-get clean

USER airflow
COPY requirements.txt .
RUN pip install -r requirements.txt