# Run from project root: uvicorn src.api.main:app --reload
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pathlib import Path
import csv
import json
import logging
from datetime import datetime
from src.api.schemas import UserCreate, TransactionCreate
from src.config import config
from src.streaming.kafka_producer import TransactionProducer

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="RecoMart Streaming API")

# Initialize Kafka Producer
# Use TransactionProducer for both users and transactions since it acts as a general producer wrapper
kafka_producer = TransactionProducer()

# Data Paths
DATA_DIR = Path(config.get('data_dir', 'data'))
DATA_DIR.mkdir(exist_ok=True)

# Staging files
USERS_FILE = DATA_DIR / "users_api_staging.csv"
TRANSACTIONS_FILE = DATA_DIR / "transactions_api_staging.csv"

# Initialize files with headers
def init_files():
    if not USERS_FILE.exists():
        with open(USERS_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['user_id', 'age', 'gender', 'device'])
            
    if not TRANSACTIONS_FILE.exists():
        with open(TRANSACTIONS_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['user_id', 'item_id', 'view_mode', 'rating', 'timestamp'])

init_files()

@app.post("/users", status_code=201)
async def create_user(user: UserCreate):
    """
    Public entry point for user registration.
    Sends user data to Kafka 'recomart-users' topic.
    """
    try:
        user_data = user.dict()
        success = kafka_producer.send_event(user_data, topic='recomart-users')
        if not success:
            raise Exception("Failed to send user event to Kafka")
        
        logger.info(f"Published user {user.user_id} to Kafka")
        return {"status": "accepted", "user_id": user.user_id}
    except Exception as e:
        logger.error(f"Error publishing user: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process user data")

@app.post("/transactions", status_code=201)
async def create_transaction(transaction: TransactionCreate):
    """
    Public entry point for transaction events.
    Sends transaction data to Kafka 'recomart-transactions' topic.
    """
    try:
        tx_data = transaction.dict()
        if tx_data['timestamp']:
            tx_data['timestamp'] = tx_data['timestamp'].isoformat()
        else:
            tx_data['timestamp'] = datetime.now().isoformat()
        
        success = kafka_producer.send_event(tx_data, topic='recomart-transactions')
        if not success:
            raise Exception("Failed to send transaction event to Kafka")

        logger.info(f"Published transaction for user {transaction.user_id} to Kafka")
        return {"status": "accepted", "user_id": transaction.user_id}
    except Exception as e:
        logger.error(f"Error publishing transaction: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process transaction data")

# --- INTERNAL ENDPOINTS FOR KAFKA CONSUMER ---

@app.post("/internal/ingest-user", status_code=200)
async def internal_ingest_user(user: UserCreate):
    """
    Internal endpoint called by Kafka Consumer.
    Writes user data to CSV file.
    """
    try:
        row = [user.user_id, user.age, user.gender, user.device]
        with open(USERS_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)
        logger.info(f"INTERNAL: Ingested user {user.user_id} to CSV")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Internal ingestion error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal storage failure")

@app.post("/internal/ingest-transaction", status_code=200)
async def internal_ingest_transaction(transaction: TransactionCreate):
    """
    Internal endpoint called by Kafka Consumer.
    Writes transaction data to CSV file.
    """
    try:
        timestamp = transaction.timestamp.isoformat() if transaction.timestamp else datetime.now().isoformat()
        row = [transaction.user_id, transaction.item_id, transaction.view_mode, transaction.rating, timestamp]
        with open(TRANSACTIONS_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)
        logger.info(f"INTERNAL: Ingested transaction for user {transaction.user_id} to CSV")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Internal ingestion error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal storage failure")

@app.get("/health")
def health_check():
    return {"status": "healthy"}
