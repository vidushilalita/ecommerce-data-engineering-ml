# Apache Kafka Setup Guide for Windows

## Overview

This guide covers setting up Apache Kafka for real-time transaction streaming in the RecoMart data pipeline.

## Architecture

```
Web/Mobile App → Kafka Producer → Kafka Topic → Kafka Consumer → Data Lake → Feature Store → Model
```

---

## Prerequisites

- Java 8+ (Kafka requires Java)
- Python 3.8+
- kafka-python installed

## Installation

### 1. Install Java

```powershell
# Download and install Java 8+ from Oracle or AdoptOpenJDK
# Verify installation
java -version
```

### 2. Download Kafka

```powershell
# Download Kafka from https://kafka.apache.org/downloads
# Example: kafka_2.13-3.6.0.tgz

# Extract to a directory
# Example: C:\kafka
```

### 3. Configure Kafka

Edit `config/kraft/server.properties`:

```properties
# Kafka broker configuration
node.id=1
process.roles=broker,controller
inter.broker.listener.name=PLAINTEXT
controller.listener.names=CONTROLLER
listeners=PLAINTEXT://localhost:9092,CONTROLLER://localhost:9093
controller.quorum.voters=1@localhost:9093

# Log directory (Use forward slashes even on Windows)
# Windows Example: C:/kafka/kafka-logs
# Linux/Mac Example: /tmp/kafka-logs
log.dirs=/tmp/kafka-logs
```

---

## Running Kafka (KRaft Mode)

### 1. Generate Cluster ID

**Windows (PowerShell)**:
```powershell
cd C:\kafka
.\bin\windows\kafka-storage.bat random-uuid
# Copy the output UUID (e.g., 87x547845-x8457)
```

**Linux / Mac**:
```bash
cd /usr/local/kafka
./bin/kafka-storage.sh random-uuid
# Copy the output UUID
```

### 2. Format Log Directories

Replace `<CLUSTER_ID>` with the UUID generated in step 1.

**Windows**:
```powershell
.\bin\windows\kafka-storage.bat format -t <CLUSTER_ID> -c .\config\kraft\server.properties
```

**Linux / Mac**:
```bash
./bin/kafka-storage.sh format -t <CLUSTER_ID> -c config/kraft/server.properties
```

### 3. Start Kafka Server

**Windows (Terminal 1)**:
```powershell
.\bin\windows\kafka-server-start.bat .\config\kraft\server.properties
```

**Linux / Mac (Terminal 1)**:
```bash
./bin/kafka-server-start.sh config/kraft/server.properties
```

### 4. Create Topic (Terminal 2)

**Windows**:
```powershell
.\bin\windows\kafka-topics.bat --create `
    --topic recomart-transactions `
    --bootstrap-server localhost:9092 `
    --partitions 3 `
    --replication-factor 1
```

**Linux / Mac**:
```bash
./bin/kafka-topics.sh --create \
    --topic recomart-transactions \
    --bootstrap-server localhost:9092 \
    --partitions 3 \
    --replication-factor 1
```

### 5. Verify Topic

**Windows**:
```powershell
# List topics
.\bin\windows\kafka-topics.bat --list --bootstrap-server localhost:9092

# Describe topic
.\bin\windows\kafka-topics.bat --describe --topic recomart-transactions --bootstrap-server localhost:9092
```

**Linux / Mac**:
```bash
# List topics
./bin/kafka-topics.sh --list --bootstrap-server localhost:9092

# Describe topic
./bin/kafka-topics.sh --describe --topic recomart-transactions --bootstrap-server localhost:9092
```

---

## Usage

### Start Producer (Terminal 3)

**Windows**:
```powershell
cd C:\Users\Vidushi.Bisht\Documents\ecommerce-data-engineering-ml
.\venv\Scripts\Activate.ps1
python src/streaming/kafka_producer.py
```

**Linux / Mac**:
```bash
cd ~/ecommerce-data-engineering-ml
source venv/bin/activate
python src/streaming/kafka_producer.py
```

### Start Consumer (Terminal 4)

**Windows**:
```powershell
.\venv\Scripts\Activate.ps1
python src/streaming/kafka_consumer.py
```

**Linux / Mac**:
```bash
source venv/bin/activate
python src/streaming/kafka_consumer.py
```

---

## Monitoring

### Kafka Console Consumer

**Windows**:
```powershell
.\bin\windows\kafka-console-consumer.bat --topic recomart-transactions --bootstrap-server localhost:9092 --from-beginning
```

**Linux / Mac**:
```bash
./bin/kafka-console-consumer.sh --topic recomart-transactions --bootstrap-server localhost:9092 --from-beginning
```

### Check Consumer Group Lag

**Windows**:
```powershell
.\bin\windows\kafka-consumer-groups.bat --bootstrap-server localhost:9092 --describe --group recomart-consumer-group
```

**Linux / Mac**:
```bash
./bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group recomart-consumer-group
```

### View Logs

**Windows**:
```powershell
Get-Content logs\src_streaming_kafka_consumer.log -Tail 50
```

**Linux / Mac**:
```bash
tail -f logs/src_streaming_kafka_consumer.log
```

---

## Architecture Components

### Producer (`kafka_producer.py`)

**Purpose**: Simulate real-time transaction events

**Features**:
- Creates transaction events (view, add_to_cart, purchase)
- Publishes to Kafka topic
- Configurable event rate
- Error handling and retries

### Consumer (`kafka_consumer.py`)

**Purpose**: Process streaming transactions in real-time

**Features**:
- Consumes from Kafka topic
- Processes events (add implicit scores, timestamps)
- Batches events (buffer_size=100)
- Stores in data lake (streaming layer)
- Auto-commit offsets

---

## Integration with Pipeline

### Real-time Feature Updates

```python
# After consumer stores streaming data
# Update feature store with new interactions
from src.features.feature_store import SimpleFeatureStore
from src.utils.storage import DataLakeStorage
# ... logic to update features
```


---

## Airflow Integration

### Streaming DAG

Create `airflow/dags/dag_streaming.py`:

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

def run_consumer():
    from src.streaming.kafka_consumer import TransactionConsumer
    consumer = TransactionConsumer()
    consumer.consume_stream(max_messages=1000)
    consumer.close()

dag = DAG(
    'streaming_consumer',
    schedule_interval='*/5 * * * *',  # Every 5 minutes
    start_date=datetime(2026, 1, 22),
    catchup=False
)

task = PythonOperator(
    task_id='consume_transactions',
    python_callable=run_consumer,
    dag=dag
)
```

---

## Production Considerations

### 1. Scaling

**Multiple Partitions**: Increase parallelism
```powershell
--partitions 10
```

**Multiple Consumers**: Scale consumer group
```python
# Run multiple consumer instances with same group_id
```

### 2. Fault Tolerance

**Replication**: Increase replication factor
```powershell
--replication-factor 3
```

**Acknowledgments**: Configure producer acks
```python
acks='all'  # Wait for all replicas
```

### 3. Performance

**Batching**: Adjust batch size
```python
batch_size=16384  # Producer batch size
buffer_size=1000  # Consumer buffer
```

**Compression**: Enable compression
```python
compression_type='gzip'
```

---

## Troubleshooting

### Issue: Inconsistent Cluster ID
**Solution**:
If you receive `InconsistentClusterIdException`, it means the log directory was formatted with a different cluster ID than the one currently expected.
```powershell
# Clean up log directory (WARNING: DELETES DATA)
Remove-Item -Recurse -Force C:\tmp\kafka-logs
# Re-format
.\bin\windows\kafka-storage.bat format ...
```

### Issue: Topic not found

**Solution**:
```powershell
# Recreate topic
.\bin\windows\kafka-topics.bat --create --topic recomart-transactions ...
```

### Issue: Consumer lag

**Solution**:
- Increase number of partitions
- Add more consumer instances
- Increase buffer size

### Issue: Connection refused

**Solution**:
- Verify Kafka is running
- Check `listeners` in server.properties
- Ensure firewall allows port 9092

---

## File Structure

```
ecommerce-data-engineering-ml/
├── src/
│   └── streaming/
│       ├── __init__.py
│       ├── kafka_producer.py    # Event producer
│       └── kafka_consumer.py    # Event consumer
├── storage/
│   └── streaming/               # Streaming data layer
│       └── transactions/
└── docs/
    └── KAFKA_SETUP.md           # This file
```

---

## Benefits

- ✅ **Real-time processing**: Near-instant feature updates
- ✅ **Scalability**: Handle high-velocity data streams
- ✅ **Fault tolerance**: Durable message queue
- ✅ **Decoupling**: Producer/consumer independence
- ✅ **Replay capability**: Re-process historical events

---

## Next Steps

1. **Run the streaming pipeline**: Start Kafka (KRaft), Producer, Consumer
2. **Monitor events**: Use console consumer to verify flow
3. **Integrate with features**: Update feature store in real-time
4. **Deploy model serving**: Enable real-time recommendations
5. **Add monitoring**: Set up metrics and alerting

---

## Resources

- [Kafka Documentation](https://kafka.apache.org/documentation/)
- [kafka-python](https://kafka-python.readthedocs.io/)
- [Kafka on Windows](https://kafka.apache.org/quickstart)
