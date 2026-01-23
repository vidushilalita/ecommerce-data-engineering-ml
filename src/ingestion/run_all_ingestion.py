"""
Master ingestion script - runs all data ingestion tasks

This script orchestrates the ingestion of all data sources:
- Users (users1.csv + users2.csv)
- Products (products.json)
- Transactions (transactions.csv)
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.ingestion.ingest_users import UserDataIngestion
from src.ingestion.ingest_products import ProductDataIngestion
from src.ingestion.ingest_transactions import TransactionDataIngestion
from src.utils.logger import get_logger

logger = get_logger(__name__)


def run_all_ingestion():
    """Run all data ingestion tasks"""
    logger.info("=" * 70)
    logger.info("STARTING MASTER DATA INGESTION PIPELINE")
    logger.info("=" * 70)
    
    results = {}
    errors = []
    
    # 1. Ingest Users
    try:
        logger.info("\n[1/3] Ingesting User Data...")
        user_ingestion = UserDataIngestion()
        results['users'] = user_ingestion.ingest()
    except Exception as e:
        logger.error(f" Failed user ingestion: {str(e)}")
        errors.append(('users', str(e)))
    
    # 2. Ingest Products
    try:
        logger.info("\n[2/3] Ingesting Product Data...")
        product_ingestion = ProductDataIngestion()
        results['products'] = product_ingestion.ingest()
    except Exception as e:
        logger.error(f"✗ Failed product ingestion: {str(e)}")
        errors.append(('products', str(e)))
    
    # 3. Ingest Transactions
    try:
        logger.info("\n[3/3] Ingesting Transaction Data...")
        transaction_ingestion = TransactionDataIngestion()
        results['transactions'] = transaction_ingestion.ingest()
    except Exception as e:
        logger.error(f"✗ Failed transaction ingestion: {str(e)}")
        errors.append(('transactions', str(e)))
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("INGESTION SUMMARY")
    logger.info("=" * 70)
    
    for source, metadata in results.items():
        logger.info(f"✓ {source.upper()}:")
        logger.info(f"  Records: {metadata['record_count']:,}")
        logger.info(f"  Size: {metadata['file_size_bytes']:,} bytes")
    
    if errors:
        logger.error(f"\n✗ {len(errors)} ingestion(s) failed:")
        for source, error in errors:
            logger.error(f"  - {source}: {error}")
    else:
        logger.info("\n✓ All ingestions completed successfully!")
    
    logger.info("=" * 70)
    
    return len(errors) == 0


if __name__ == '__main__':
    success = run_all_ingestion()
    sys.exit(0 if success else 1)
