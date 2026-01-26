"""
Transaction data ingestion module

Ingests transaction data from CSV files containing "transaction" in the name,
parses timestamps, validates interactions, and stores in partitioned raw storage.
"""

import os
import sys
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.logger import get_logger
from src.utils.storage import DataLakeStorage

logger = get_logger(__name__)


class TransactionDataIngestion:
    """Handles ingestion of transaction/interaction data from CSV sources"""
    
    def __init__(self, data_dir: str = 'data', storage_base: str = 'storage'):
        """
        Initialize transaction data ingestion
        
        Args:
            data_dir: Directory containing source data files
            storage_base: Base directory for data lake storage
        """
        self.data_dir = Path(data_dir)
        self.storage = DataLakeStorage(storage_base)
        self.transaction_files = self.discover_source_files()
        logger.info(f"Initialized TransactionDataIngestion with data_dir={data_dir}")

    def discover_source_files(self) -> List[str]:
        """
        Discover CSV files containing 'transaction' in the name
        
        Returns:
            List of filenames
        """
        if not self.data_dir.exists():
            logger.warning(f"Data directory {self.data_dir} does not exist")
            return []
            
        discovered = [
            f.name for f in self.data_dir.glob("*.csv") 
            if "transaction" in f.name.lower()
        ]
        
        if discovered:
            logger.info(f" Discovered {len(discovered)} transaction data files: {discovered}")
        else:
            logger.warning(" No files containing 'transaction' found in data directory")
            
        return discovered
    
    def validate_source_files(self) -> Dict[str, bool]:
        """
        Validate that source files exist and are accessible
        
        Returns:
            Dictionary mapping filename to existence status
        """
        validation_results = {}
        
        if not self.transaction_files:
            logger.error("No transaction files discovered to validate")
            return {}

        for filename in self.transaction_files:
            file_path = self.data_dir / filename
            exists = file_path.exists()
            validation_results[filename] = exists
            
            if exists:
                file_size = os.path.getsize(file_path)
                logger.info(f" Found {filename} ({file_size:,} bytes)")
            else:
                logger.error(f"✗ Missing {filename}")
        
        return validation_results
    
    def read_transaction_csv(self, filename: str) -> pd.DataFrame:
        """
        Read a single transaction CSV file with error handling
        
        Args:
            filename: Name of CSV file to read
        
        Returns:
            DataFrame with transaction data
        """
        file_path = self.data_dir / filename
        
        try:
            df = pd.read_csv(file_path)
            logger.info(f"Read {len(df)} transactions from {filename}")
            return df
        
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise
        
        except pd.errors.EmptyDataError:
            logger.error(f"File is empty: {file_path}")
            raise
        
        except Exception as e:
            logger.error(f"Error reading {filename}: {str(e)}")
            raise
    
    def merge_transaction_data(self, dfs: List[pd.DataFrame]) -> pd.DataFrame:
        """Merge multiple transaction dataframes"""
        if not dfs:
            return pd.DataFrame()
        return pd.concat(dfs, ignore_index=True)

    def parse_timestamps(self, df: pd.DataFrame) -> pd.DataFrame:
        """Parse timestamp column to datetime"""
        if 'timestamp' in df.columns:
            try:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                logger.info(" Parsed timestamps successfully")
            except Exception as e:
                logger.error(f"Error parsing timestamps: {str(e)}")
        return df
    
    def validate_transaction_data(self, df: pd.DataFrame) -> None:
        """Perform basic validation on transaction data"""
        if df.empty: return
        
        expected_columns = {'user_id', 'item_id', 'view_mode', 'rating', 'timestamp'}
        missing_columns = expected_columns - set(df.columns)
        
        if missing_columns:
            logger.warning(f"Missing expected columns: {missing_columns}")
        
        if 'view_mode' in df.columns:
            valid_modes = {'view', 'add_to_cart', 'purchase'}
            actual_modes = set(df['view_mode'].unique())
            invalid_modes = actual_modes - valid_modes
            if invalid_modes:
                logger.warning(f"Found invalid view_mode values: {invalid_modes}")
        
        logger.info(" Validation complete")
    
    def ingest(self) -> Dict[str, Any]:
        """Execute complete transaction data ingestion pipeline"""
        logger.info("=" * 60)
        logger.info("Starting Transaction Data Ingestion (Dynamic)")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        # Step 1: Validate source files
        self.validate_source_files()
        
        if not self.transaction_files:
            logger.warning("No transaction files found to ingest")
            return {'record_count': 0, 'file_path': 'None', 'file_size_bytes': 0}

        # Step 2: Read all files
        dfs = []
        for filename in self.transaction_files:
            dfs.append(self.read_transaction_csv(filename))
            
        # Step 3: Merge
        df = self.merge_transaction_data(dfs)
        
        if df.empty:
            logger.warning("No transaction data were processed")
            return {'record_count': 0, 'file_path': 'None', 'file_size_bytes': 0}

        # Step 4: Parse & Validate
        df = self.parse_timestamps(df)
        self.validate_transaction_data(df)
        
        # Step 5: Store
        metadata = self.storage.save_dataframe(
            df=df,
            source='transactions',
            data_type='raw',
            filename='transactions_merged',
            format='parquet'
        )
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        logger.info("=" * 60)
        logger.info(f" Transaction ingestion completed in {execution_time:.2f} seconds")
        logger.info(f"  Records ingested: {metadata['record_count']:,}")
        logger.info(f"  Storage path: {metadata['file_path']}")
        logger.info("=" * 60)
        
        return metadata


def main():
    """Main execution function"""
    try:
        ingestion = TransactionDataIngestion()
        metadata = ingestion.ingest()
        
        print("\n Transaction data ingestion successful!")
        print(f"Records: {metadata['record_count']:,}")
        print(f"Location: {metadata['file_path']}")
        
        return 0
    
    except Exception as e:
        logger.critical(f"Transaction ingestion failed: {str(e)}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
