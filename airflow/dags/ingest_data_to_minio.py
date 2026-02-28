import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
from io import BytesIO
from minio import Minio

def upload_to_minio():
    df = pd.read_csv("/opt/airflow/data/raw_dataset.csv")
    
    buffer = BytesIO()
    df.to_parquet(buffer, index=False) # save to buffer instead of disk since it will eventually go straight to minio
    buffer.seek(0)

    # create a MinIO client
    client = Minio(
        "minio:9000",
        access_key="admin",
        secret_key="password123",
        secure=False
    )

    bucket = "bronze"
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
        print("Created")
    else:
        print("Already exists")

    # Upload the file, renaming it in the process
    client.put_object(
        bucket, 
        object_name="bronze.parquet",
        data=buffer,
        length=buffer.getbuffer().nbytes,
    )

with DAG(
    dag_id="ingest_data_to_minio",
    start_date=datetime(2024, 1, 1),
    schedule=None,          # ← important
    catchup=False,
)  as dag:
    test_task = PythonOperator(
        task_id="upload_csv_to_minio",
        python_callable=upload_to_minio
    )