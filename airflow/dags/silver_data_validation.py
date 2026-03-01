from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from datetime import datetime

with DAG(
    dag_id="silver_data_validation",
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False
) as dag:
    batch_processing_task = SparkSubmitOperator(
        task_id="data_validation",
        application="/opt/spark/scripts/data_validation.py",
        conn_id="spark_default",
        jars="/opt/bitnami/spark/jars/extra/hadoop-aws-3.3.4.jar,"
         "/opt/bitnami/spark/jars/extra/aws-java-sdk-bundle-1.12.262.jar,"
         "/opt/bitnami/spark/jars/extra/iceberg-spark-runtime-3.5_2.12-1.5.2.jar",
        verbose=True
    )