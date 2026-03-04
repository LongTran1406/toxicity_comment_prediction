from pyflink.datastream import StreamExecutionEnvironment
# CHANGE: Import MapFunction instead of RichMapFunction
from pyflink.datastream.functions import MapFunction 
from pyflink.table import StreamTableEnvironment, EnvironmentSettings
import redis

# CHANGE: Inherit from MapFunction (it still supports open/close in PyFlink)
class FeatureExtractor(MapFunction):
    def open(self, runtime_context):
        self.r = redis.Redis(host='redis', port=6379, decode_responses=True)

    def map(self, row):
        id = row[0]
        message = row[2]
        comment_length = len(message)
        uppercase_ratio = sum(1 for c in message if c.isupper()) / max(comment_length, 1)
        exclamation_count = message.count("!")
        toxic_word_count = int("stupid" in message.lower())

        self.r.hset(f"comment:{id}", mapping={
            "comment_text": message,
            "comment_length": comment_length,
            "uppercase_ratio": uppercase_ratio,
            "exclamation_count": exclamation_count,
            "toxic_word_count": toxic_word_count
        })
        return row

r = redis.Redis(host='redis', port=6379, decode_responses=True)

env = StreamExecutionEnvironment.get_execution_environment()
settings = EnvironmentSettings.new_instance().in_streaming_mode().build()
t_env = StreamTableEnvironment.create(env, environment_settings=settings)

t_env.execute_sql("""
    CREATE TABLE kafka_source (
        id STRING,
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

table = t_env.from_path("kafka_source")
ds = t_env.to_data_stream(table)
ds = ds.map(FeatureExtractor())

env.execute("Online Feature Store Job")