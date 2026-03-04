from pyarrow import fs
import pyarrow.parquet as pq

from data_cleaning import DataCleaning
from train import Training

# Connect to MinIO
minio_fs = fs.S3FileSystem(
    endpoint_override="http://minio:9000",
    access_key="admin",
    secret_key="password123",
)

# Load dataset
dataset = pq.read_table(
    "warehouse/gold.db/comment_features/data",
    filesystem=minio_fs
)

df = dataset.to_pandas()

# Select required columns
df_selected = df[["comment_text", "toxicity"]]
print(df.shape)

# Dataset cleaning
cleaner = DataCleaning(df_selected)
df_cleaned = cleaner.run()

# Train
trainer = Training(
    df=df_cleaned,
    thresholds=[0.5],
    tracking_uri="http://localhost:5000"
)

trainer.training()