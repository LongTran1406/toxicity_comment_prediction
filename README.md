# toxicity_comment_prediction
nyc-taxi-feature-store/
├── airflow/
├── spark/
├── flink/
├── kafka/
├── feature_store/
├── training/
├── serving/
│   ├── fastapi/
│   ├── docker-compose.yml
│   └── k8s/
├── monitoring/
│   ├── prometheus/
│   ├── grafana/
│   └── jaeger/
├── jenkins/
├── notebooks/
│   ├── 01_eda.ipynb
│   ├── 02_processing.ipynb
│   ├── 03_modeling.ipynb
│   └── 04_prepare_deploy.ipynb
└── README.md

----------

PHASE 2 – BATCH INGESTION (MINIO – BRONZE)
🎯 Mục tiêu phase 2

Lấy NYC Taxi (sample nhỏ)

Đưa vào MinIO

Chạy bằng Airflow

Lưu dạng Parquet

📁 Cấu trúc repo (tối thiểu)

airflow/
├── dags/
│   └── ingest_taxi_to_minio.py
├── docker-compose.yml
└── requirements.txt

data/
└── yellow_tripdata_sample.csv

PHASE 3 – SPARK BATCH PROCESSING (BASIC)
🎯 Mục tiêu phase 3

Dùng Apache Spark

Đọc dữ liệu Bronze (MinIO)

Clean dữ liệu tối thiểu

Tạo vài feature đơn giản

Ghi ra Silver Zone

spark/
├── batch_to_silver.py
└── docker-compose.yml  

