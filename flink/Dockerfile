FROM apache/flink:latest

USER root
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/* && ln -s /usr/bin/python3 /usr/bin/python
USER flink

WORKDIR /opt/flink/conf

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY jobs/*.py /opt/flink/conf/

ENTRYPOINT ["flink", "run", "--python", "kafka_to_clickhouse_flink.py", "/opt/flink/lib/flink-connector-kafka_2.12-1.16.0.jar"]