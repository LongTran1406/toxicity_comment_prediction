from pyspark.sql import SparkSession
import great_expectations as gx

spark = SparkSession.builder \
    .appName("Data Validation") \
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

df_pandas = spark.sql("SELECT * FROM hive_catalog.silver.comments").toPandas()

context = gx.get_context(mode="file", project_root_dir="/tmp/gx")

data_source = context.data_sources.add_pandas(name="pandas_datasource")
data_asset = data_source.add_dataframe_asset(name="silver_comments")
batch_definition = data_asset.add_batch_definition_whole_dataframe("batch")

suite = context.suites.add(gx.ExpectationSuite(name="silver_suite"))
suite.add_expectation(gx.expectations.ExpectColumnToExist(column="comment_text"))
suite.add_expectation(gx.expectations.ExpectColumnToExist(column="severe_toxicity"))
suite.add_expectation(gx.expectations.ExpectColumnToExist(column="obscene"))
suite.add_expectation(gx.expectations.ExpectColumnToExist(column="sexual_explicit"))
suite.add_expectation(gx.expectations.ExpectColumnToExist(column="identity_attack"))
suite.add_expectation(gx.expectations.ExpectColumnToExist(column="insult"))
suite.add_expectation(gx.expectations.ExpectColumnToExist(column="threat"))
suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="comment_text"))
suite.add_expectation(gx.expectations.ExpectColumnValuesToBeUnique(column="comment_text"))

validation_definition = context.validation_definitions.add(
    gx.ValidationDefinition(name="silver_validation", data=batch_definition, suite=suite)
)

result = validation_definition.run(batch_parameters={"dataframe": df_pandas})

context.build_data_docs()

if not result["success"]:
    raise ValueError("Data validation failed")

print("Data validation passed")