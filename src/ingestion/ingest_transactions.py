"""
Transaction data ingestion module

Ingests transaction data from CSV, parses timestamps, validates interactions,
and stores in partitioned raw storage with metadata tracking.
"""

import os
import sys
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.logger import get_logger
from src.utils.storage import DataLakeStorage

logger = get_logger(__name__)


class TransactionDataIngestion:
    """Handles ingestion of transaction/interaction data from CSV source"""
    
    def __init__(self, data_dir: str = 'data', storage_base: str = 'storage'):
        """
        Initialize transaction data ingestion
        
        Args:
            data_dir: Directory containing source data files
            storage_base: Base directory for data lake storage
        """
        self.data_dir = Path(data_dir)
        self.storage = DataLakeStorage(storage_base)
        self.transaction_file = 'transactions.csv'
        logger.info(f"Initialized TransactionDataIngestion with data_dir={data_dir}")
    
    def validate_source_file(self) -> bool:
        """
        Validate that source file exists and is accessible
        
        Returns:
            True if file exists, raises exception otherwise
        """
        file_path = self.data_dir / self.transaction_file
        
        if not file_path.exists():
            logger.error(f"✗ Missing {self.transaction_file}")
            raise FileNotFoundError(f"Transaction file not found: {file_path}")
        
        file_size = os.path.getsize(file_path)
        logger.info(f" Found {self.transaction_file} ({file_size:,} bytes)")
        
        return True
    
    def read_transaction_csv(self) -> pd.DataFrame:
        """
        Read transaction CSV file with error handling
        
        Returns:
            DataFrame with transaction data
        """
        file_path = self.data_dir / self.transaction_file
        
        try:
            # Read CSV with timestamp parsing
            df = pd.read_csv(file_path)
            
            logger.info(f"Read {len(df)} transactions from CSV")
            logger.debug(f"Columns: {df.columns.tolist()}")
            
            return df
        
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise
        
        except pd.errors.EmptyDataError:
            logger.error(f"File is empty: {file_path}")
            raise
        
        except Exception as e:
            logger.error(f"Error reading {self.transaction_file}: {str(e)}")
            raise
    
    def parse_timestamps(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Parse timestamp column to datetime
        
        Args:
            df: Transaction DataFrame
        
        Returns:
            DataFrame with parsed timestamps
        """
        logger.info("Parsing timestamps...")
        
        if 'timestamp' in df.columns:
            try:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                logger.info(f" Parsed timestamps successfully")
                
                # Log time range
                min_time = df['timestamp'].min()
                max_time = df['timestamp'].max()
                logger.info(f"  Time range: {min_time} to {max_time}")
                
            except Exception as e:
                logger.error(f"Error parsing timestamps: {str(e)}")
                raise
        else:
            logger.warning("No 'timestamp' column found")
        
        return df
    
    def validate_transaction_data(self, df: pd.DataFrame) -> None:
        """
        Perform validation on transaction data
        
        Args:
            df: Transaction DataFrame to validate
        """
        logger.info("Validating transaction data...")
        
        # Expected columns
        expected_columns = {'user_id', 'item_id', 'view_mode', 'rating', 'timestamp'}
        missing_columns = expected_columns - set(df.columns)
        
        if missing_columns:
            logger.warning(f"Missing expected columns: {missing_columns}")
        
        # Validate view_mode values
        if 'view_mode' in df.columns:
            valid_modes = {'view', 'add_to_cart', 'purchase'}
            actual_modes = set(df['view_mode'].unique())
            invalid_modes = actual_modes - valid_modes
            
            if invalid_modes:
                logger.warning(f"Found invalid view_mode values: {invalid_modes}")
            
            # Log distribution
            mode_dist = df['view_mode'].value_counts()
            logger.info(f"Interaction distribution:\n{mode_dist}")
        
        # Validate rating range
        if 'rating' in df.columns:
            min_rating = df['rating'].min()
            max_rating = df['rating'].max()
            
            if min_rating < 1 or max_rating > 5:
                logger.warning(f"Ratings outside expected range [1-5]: min={min_rating}, max={max_rating}")
        
        # Check for nulls
        null_counts = df.isnull().sum()
        if null_counts.sum() > 0:
            logger.info(f"Null value counts:\n{null_counts[null_counts > 0]}")
        
        logger.info(" Validation complete")
    
    def ingest(self) -> Dict[str, Any]:
        """
        Execute complete transaction data ingestion pipeline
        
        Returns:
            Metadata dictionary from storage operation
        """
        logger.info("=" * 60)
        logger.info("Starting Transaction Data Ingestion")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        # Step 1: Validate source file
        logger.info("Step 1: Validating source file...")
        self.validate_source_file()
        
        # Step 2: Read CSV data
        logger.info("Step 2: Reading transaction CSV...")
        df = self.read_transaction_csv()
        
        # Step 3: Parse timestamps
        logger.info("Step 3: Parsing timestamps...")
        df = self.parse_timestamps(df)
        
        # Step 4: Validate data
        logger.info("Step 4: Validating transaction data...")
        self.validate_transaction_data(df)
        
        # Step 5: Store in data lake
        logger.info("Step 5: Storing in partitioned data lake...")
        metadata = self.storage.save_dataframe(
            df=df,
            source='transactions',
            data_type='raw',
            filename='transactions',
            format='parquet'
        )
        
        # Calculate execution time
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        logger.info("=" * 60)
        logger.info(f" Transaction ingestion completed in {execution_time:.2f} seconds")
        logger.info(f"  Records ingested: {metadata['record_count']:,}")
        logger.info(f"  File size: {metadata['file_size_bytes']:,} bytes")
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
