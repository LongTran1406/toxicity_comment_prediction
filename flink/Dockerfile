FROM flink:1.18.1-scala_2.12

USER root
RUN apt-get update -y && \
    apt-get install -y python3 python3-pip && \
    pip3 install apache-flink==1.18.1 && \
    pip3 install apache-flink==1.18.0 redis && \
    ln -s /usr/bin/python3 /usr/bin/python

COPY ./jars/flink-sql-connector-kafka-3.0.1-1.18.jar /opt/flink/lib/
COPY ./jars/flink-sql-parquet-1.18.1.jar /opt/flink/lib/
COPY ./jars/flink-s3-fs-hadoop-1.18.1.jar /opt/flink/lib/
COPY ./jars/hadoop-mapreduce-client-core-3.3.4.jar /opt/flink/lib/

USER flink