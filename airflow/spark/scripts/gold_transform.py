from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.sql.functions import (
    length, split, size, regexp_replace,
    col, when, current_timestamp, sha2
)


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

df_silver = spark.read.table("hive_catalog.silver.comments")
print(df_silver.head())


df_gold = df_silver.select(
    sha2(col("comment_text"), 256).alias("comment_id"),
    col("comment_text"),
    length("comment_text").alias("comment_length"),
    size(split(col("comment_text"), " ")).alias("word_count"),
    (
        length(regexp_replace("comment_text", "[^A-Z]", ""))
        / when(length("comment_text") == 0, 1)
          .otherwise(length("comment_text"))
    ).alias("uppercase_ratio"),
    (
        length("comment_text") -
        length(regexp_replace("comment_text", "!", ""))
    ).alias("exclamation_count"),
    col("toxicity"),
    when(col("toxicity") > 0.5, 1).otherwise(0).alias("is_toxic"),
    current_timestamp().alias("feature_timestamp")
)
spark.sql("CREATE DATABASE IF NOT EXISTS hive_catalog.gold")

df_gold.writeTo("hive_catalog.gold.comment_features") \
    .tableProperty("write.format.default", "parquet") \
    .createOrReplace()