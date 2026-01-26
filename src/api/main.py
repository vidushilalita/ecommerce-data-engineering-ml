# Run from project root: uvicorn src.api.main:app --reload
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pathlib import Path
import csv
import json
import logging
from datetime import datetime
from src.api.schemas import UserCreate, TransactionCreate
from src.config import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="RecoMart Ingestion API")

# Data Paths
DATA_DIR = Path(config.get('data_dir', 'data'))
DATA_DIR.mkdir(exist_ok=True)

# We use append mode for CSVs to act as a log
USERS_FILE = DATA_DIR / "users_api_staging.csv"
TRANSACTIONS_FILE = DATA_DIR / "transactions_api_staging.csv"

# Initialize files with headers if they don't exist
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
async def create_user(user: UserCreate, background_tasks: BackgroundTasks):
    """
    Create a new user.
    Appends to a staging CSV file which will be picked up by the batch pipeline.
    """
    try:
        # Prepare row
        row = [
            user.user_id,
            user.age,
            user.gender,
            user.device
        ]
        
        # Append to file (simple file lock mechanism would be improved in prod)
        with open(USERS_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)
            
        logger.info(f"Ingested user {user.user_id}")
        return {"status": "success", "user_id": user.user_id}
        
    except Exception as e:
        logger.error(f"Error ingesting user: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to store user data")

@app.post("/transactions", status_code=201)
async def create_transaction(transaction: TransactionCreate):
    """
    Record a transaction (view, cart, purchase).
    Appends to a staging CSV file.
    """
    try:
        row = [
            transaction.user_id,
            transaction.item_id,
            transaction.view_mode,
            transaction.rating,
            transaction.timestamp.isoformat() if transaction.timestamp else datetime.now().isoformat()
        ]
        
        with open(TRANSACTIONS_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)
            
        logger.info(f"Ingested transaction for user {transaction.user_id} - {transaction.view_mode}")
        return {"status": "success", "event_id": f"{transaction.user_id}-{transaction.item_id}-{datetime.now().timestamp()}"}
        
    except Exception as e:
        logger.error(f"Error ingesting transaction: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to store transaction data")

@app.get("/health")
def health_check():
    return {"status": "healthy"}
