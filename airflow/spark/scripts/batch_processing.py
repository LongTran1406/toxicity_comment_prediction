from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from io import BytesIO
from minio import Minio

# Iceberg catalog 3 first lines
spark = SparkSession.builder \
    .appName("Batch Silver") \
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions") \
    .config("spark.sql.catalog.hive_catalog", "org.apache.iceberg.spark.SparkCatalog") \
    .config("spark.sql.catalog.hive_catalog.type", "hive") \
    .config("spark.sql.catalog.hive_catalog.uri", "thrift://hive-metastore:9083") \
    .config("spark.sql.catalog.hive_catalog.warehouse", "s3a://warehouse/") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
    .config("spark.hadoop.fs.s3a.access.key", "admin") \
    .config("spark.hadoop.fs.s3a.secret.key", "password123") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .getOrCreate()

df = spark.read.parquet("s3a://bronze/bronze.parquet")
print(df.show())

# toxicty, severe_toxicity, obscene, sexual_explicit, identity_attack, insult, threat

df_selected = df.select(
    "comment_text",
    "toxicity",
    "severe_toxicity",
    "obscene",
    "sexual_explicit",
    "identity_attack",
    "insult",
    "threat"
)

df_clean = df_selected.filter(
    (col("toxicity") > 0) &
    (col("severe_toxicity") > 0) &
    (col("obscene") > 0) &
    (col("sexual_explicit") > 0) &
    (col("identity_attack") > 0) &
    (col("insult") > 0) &
    (col("threat") > 0)
).dropDuplicates(["comment_text"])

# Create silver bucket if not exists
client = Minio(
    "minio:9000",
    access_key="admin",
    secret_key="password123",
    secure=False
)

if not client.bucket_exists("warehouse"):
    client.make_bucket("warehouse")

spark.sql("CREATE DATABASE IF NOT EXISTS hive_catalog.silver")

df_clean.writeTo("hive_catalog.silver.comments") \
    .tableProperty("write.format.default", "parquet") \
    .createOrReplace()