from pyflink.table import TableEnvironment, EnvironmentSettings

# Use simple streaming environment — cluster config comes from flink run
settings = EnvironmentSettings.new_instance() \
    .in_streaming_mode() \
    .build()

t_env = TableEnvironment.create(settings)

# MinIO config
conf = t_env.get_config().get_configuration()
conf.set_string("s3.endpoint", "http://minio:9000")
conf.set_string("s3.access-key", "admin")
conf.set_string("s3.secret-key", "password123")
conf.set_string("s3.path.style.access", "true")
conf.set_string("fs.s3a.endpoint", "http://minio:9000")
conf.set_string("fs.s3a.access.key", "admin")
conf.set_string("fs.s3a.secret.key", "password123")
conf.set_string("fs.s3a.path.style.access", "true")
conf.set_string("fs.s3a.connection.ssl.enabled", "false")
conf.set_string("fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
conf.set_string("fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")
conf.set_string("execution.checkpointing.interval", "1 minute")


# 2. Source Definition: Kafka 'raw_data' topic
# Watermark is set to 5 seconds to handle out-of-order events
t_env.execute_sql("""
    CREATE TABLE kafka_source (
        id INT,
        user_id STRING,
        message STRING,
        ts TIMESTAMP(3),
        WATERMARK FOR ts AS ts - INTERVAL '5' SECOND
    ) WITH (
        'connector' = 'kafka',
        'topic' = 'raw_data',
        'properties.bootstrap.servers' = 'kafka:9092',
        'properties.group.id' = 'flink-group',
        'format' = 'json',
        'scan.startup.mode' = 'latest-offset'
    )
""")

# 3. Sink Definition 1: Console Print (Monitoring)
# Used for real-time debugging and monitoring windowed results in taskmanager logs
t_env.execute_sql("""
    CREATE TABLE print_sink (
        window_start TIMESTAMP(3),
        user_id STRING,
        cnt BIGINT
    ) WITH (
        'connector' = 'print'
    )
""")

# 4. Sink Definition 2: MinIO Bronze Layer (Data Lake Ingestion)
# Saves raw data in Parquet format, partitioned by date and hour for Spark Batch processing
t_env.execute_sql("""
    CREATE TABLE minio_bronze_sink (
        id INT,
        user_id STRING,
        message STRING,
        ts TIMESTAMP(3),
        `dt` STRING,
        `hr` STRING
    ) PARTITIONED BY (dt, hr) WITH (
        'connector' = 'filesystem',
        'path' = 's3a://bronze/stream_data/',
        'format' = 'parquet',
        'sink.partition-commit.policy.kind' = 'success-file'
    )
""")

# 5. Multi-Sink Execution using StatementSet
# This allows Flink to process the Kafka stream once and broadcast to multiple destinations
statement_set = t_env.create_statement_set()

# Pipeline A: Real-time Windowed Aggregation
# Calculates message count per user per 1-minute tumbling window
statement_set.add_insert_sql("""
    INSERT INTO print_sink
    SELECT 
        TUMBLE_START(ts, INTERVAL '1' MINUTE),
        user_id,
        COUNT(id)
    FROM kafka_source
    GROUP BY TUMBLE(ts, INTERVAL '1' MINUTE), user_id
""")

# Pipeline B: Data Lake Archiving (Raw Stream to Bronze)
# Persists incoming raw data into the Bronze layer with partitioning columns
statement_set.add_insert_sql("""
    INSERT INTO minio_bronze_sink
    SELECT 
        id, user_id, message, ts,
        DATE_FORMAT(ts, 'yyyy-MM-dd'),
        DATE_FORMAT(ts, 'HH')
    FROM kafka_source
""")

# Submit the multi-sink job to the Flink Cluster
# Submit the multi-sink job to the Flink Cluster
print("Submitting Job to Flink in Detached Mode...")

# This returns a TableResult immediately without waiting for the job to finish
table_result = statement_set.execute()

# Get the Job Client to extract the ID
job_client = table_result.get_job_client()

if job_client is not None:
    job_id = job_client.get_job_id()
    print(f"✅ Job successfully submitted!")
    print(f"✅ Job ID: {job_id}")
    print("You can now close this terminal. Monitor the job at http://localhost:8081")
else:
    print("❌ Job submission failed. Check JobManager logs.")