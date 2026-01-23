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

Edit `config/server.properties`:

```properties
# Kafka broker configuration
broker.id=0
listeners=PLAINTEXT://localhost:9092
log.dirs=C:/kafka/kafka-logs
num.partitions=3
offsets.topic.replication.factor=1
```

---

## Running Kafka

### 1. Start Zookeeper (Terminal 1)

```powershell
# Navigate to Kafka directory
cd C:\kafka

# Start Zookeeper
.\bin\windows\zookeeper-server-start.bat .\config\zookeeper.properties
```

### 2. Start Kafka Broker (Terminal 2)

```powershell
# Navigate to Kafka directory
cd C:\kafka

# Start Kafka server
.\bin\windows\kafka-server-start.bat .\config\server.properties
```

### 3. Create Topic (Terminal 3)

```powershell
# Create recomart-transactions topic
.\bin\windows\kafka-topics.bat --create `
    --topic recomart-transactions `
    --bootstrap-server localhost:9092 `
    --partitions 3 `
    --replication-factor 1
```

### 4. Verify Topic

```powershell
# List topics
.\bin\windows\kafka-topics.bat --list --bootstrap-server localhost:9092

# Describe topic
.\bin\windows\kafka-topics.bat --describe `
    --topic recomart-transactions `
    --bootstrap-server localhost:9092
```

---

## Usage

### Start Producer (Terminal 4)

```powershell
# Navigate to project
cd C:\Users\Vidushi.Bisht\Documents\ecommerce-data-engineering-ml

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run producer
python src/streaming/kafka_producer.py
```

**Output**: Streams simulated transaction events to Kafka

### Start Consumer (Terminal 5)

```powershell
# In another terminal (same project directory)
.\venv\Scripts\Activate.ps1

# Run consumer
python src/streaming/kafka_consumer.py
```

**Output**: Consumes events and stores in `storage/streaming/transactions/`

---

## Architecture Components

### Producer (`kafka_producer.py`)

**Purpose**: Simulate real-time transaction events

**Features**:
- Creates transaction events (view, add_to_cart, purchase)
- Publishes to Kafka topic
- Configurable event rate
- Error handling and retries

**Example**:
```python
from src.streaming.kafka_producer import TransactionProducer

producer = TransactionProducer()
producer.simulate_transaction_stream(num_events=100, delay_seconds=0.5)
producer.close()
```

### Consumer (`kafka_consumer.py`)

**Purpose**: Process streaming transactions in real-time

**Features**:
- Consumes from Kafka topic
- Processes events (add implicit scores, timestamps)
- Batches events (buffer_size=100)
- Stores in data lake (streaming layer)
- Auto-commit offsets

**Example**:
```python
from src.streaming.kafka_consumer import TransactionConsumer

consumer = TransactionConsumer()
consumer.consume_stream(max_messages=100)
consumer.close()
```

---

## Integration with Pipeline

### Real-time Feature Updates

```python
# After consumer stores streaming data
# Update feature store with new interactions

from src.features.feature_store import SimpleFeatureStore
from src.utils.storage import DataLakeStorage

storage = DataLakeStorage()
streaming_data = storage.load_latest('transactions', 'streaming')

# Recompute features incrementally
# Update feature store
```

### Near Real-time Recommendations

```python
# Use latest features for real-time predictions

from src.models.collaborative_filtering import CollaborativeFilteringModel

model = CollaborativeFilteringModel()
model.load_model('models/collaborative_filtering.pkl')

# Generate recommendations for user
recommendations = model.generate_recommendations(
    user_id=123,
    all_item_ids=item_ids,
    top_k=10
)
```

---

## Monitoring

### Kafka Console Consumer

Monitor events in real-time:

```powershell
.\bin\windows\kafka-console-consumer.bat `
    --topic recomart-transactions `
    --bootstrap-server localhost:9092 `
    --from-beginning
```

### Check Consumer Group Lag

```powershell
.\bin\windows\kafka-consumer-groups.bat `
    --bootstrap-server localhost:9092 `
    --describe `
    --group recomart-consumer-group
```

### View Logs

```powershell
# Kafka logs
Get-Content C:\kafka\logs\server.log -Tail 50

# Application logs
Get-Content logs\src_streaming_kafka_consumer.log -Tail 50
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

### Issue: Zookeeper won't start

**Solution**:
```powershell
# Clean up Zookeeper data
Remove-Item -Recurse -Force C:\kafka\zookeeper-data
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

1. **Run the streaming pipeline**: Start Zookeeper, Kafka, Producer, Consumer
2. **Monitor events**: Use console consumer to verify flow
3. **Integrate with features**: Update feature store in real-time
4. **Deploy model serving**: Enable real-time recommendations
5. **Add monitoring**: Set up metrics and alerting

---

## Resources

- [Kafka Documentation](https://kafka.apache.org/documentation/)
- [kafka-python](https://kafka-python.readthedocs.io/)
- [Kafka on Windows](https://kafka.apache.org/quickstart)
