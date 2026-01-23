"""
User data ingestion module

Ingests user data from CSV files (users1.csv and users2.csv),
merges them, and stores in partitioned raw storage with metadata tracking.
"""

import os
import sys
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.logger import get_logger
from src.utils.storage import DataLakeStorage

logger = get_logger(__name__)


class UserDataIngestion:
    """Handles ingestion of user data from CSV sources"""
    
    def __init__(self, data_dir: str = 'data', storage_base: str = 'storage'):
        """
        Initialize user data ingestion
        
        Args:
            data_dir: Directory containing source data files
            storage_base: Base directory for data lake storage
        """
        self.data_dir = Path(data_dir)
        self.storage = DataLakeStorage(storage_base)
        self.user_files = ['users1.csv', 'users2.csv']
        logger.info(f"Initialized UserDataIngestion with data_dir={data_dir}")
    
    def validate_source_files(self) -> Dict[str, bool]:
        """
        Validate that source files exist and are accessible
        
        Returns:
            Dictionary mapping filename to existence status
        """
        validation_results = {}
        
        for filename in self.user_files:
            file_path = self.data_dir / filename
            exists = file_path.exists()
            validation_results[filename] = exists
            
            if exists:
                file_size = os.path.getsize(file_path)
                logger.info(f"✓ Found {filename} ({file_size:,} bytes)")
            else:
                logger.error(f"✗ Missing {filename}")
        
        return validation_results
    
    def read_user_file(self, filename: str) -> pd.DataFrame:
        """
        Read a single user CSV file with error handling
        
        Args:
            filename: Name of CSV file to read
        
        Returns:
            DataFrame with user data
        """
        file_path = self.data_dir / filename
        
        try:
            df = pd.read_csv(file_path)
            logger.info(f"Read {len(df)} records from {filename}")
            logger.debug(f"Columns: {df.columns.tolist()}")
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
    
    def merge_user_data(self, dfs: List[pd.DataFrame]) -> pd.DataFrame:
        """
        Merge multiple user dataframes
        
        Args:
            dfs: List of user DataFrames to merge
        
        Returns:
            Combined DataFrame
        """
        logger.info(f"Merging {len(dfs)} user dataframes")
        
        # Concatenate all dataframes
        merged_df = pd.concat(dfs, ignore_index=True)
        
        logger.info(f"Merged dataset contains {len(merged_df)} total records")
        
        # Log any duplicates found
        duplicate_count = merged_df.duplicated(subset=['user_id']).sum()
        if duplicate_count > 0:
            logger.warning(f"Found {duplicate_count} duplicate user_ids in merged data")
        
        return merged_df
    
    def ingest(self) -> Dict[str, Any]:
        """
        Execute complete user data ingestion pipeline
        
        Returns:
            Metadata dictionary from storage operation
        """
        logger.info("=" * 60)
        logger.info("Starting User Data Ingestion")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        # Step 1: Validate source files
        logger.info("Step 1: Validating source files...")
        validation_results = self.validate_source_files()
        
        if not all(validation_results.values()):
            missing_files = [f for f, exists in validation_results.items() if not exists]
            raise FileNotFoundError(f"Missing required files: {missing_files}")
        
        # Step 2: Read all user files
        logger.info("Step 2: Reading user data files...")
        user_dfs = []
        
        for filename in self.user_files:
            try:
                df = self.read_user_file(filename)
                user_dfs.append(df)
            except Exception as e:
                logger.error(f"Failed to read {filename}: {str(e)}")
                raise
        
        # Step 3: Merge user data
        logger.info("Step 3: Merging user datasets...")
        merged_users = self.merge_user_data(user_dfs)
        
        # Step 4: Store in data lake
        logger.info("Step 4: Storing in partitioned data lake...")
        metadata = self.storage.save_dataframe(
            df=merged_users,
            source='users',
            data_type='raw',
            filename='users_merged',
            format='parquet'
        )
        
        # Calculate execution time
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        logger.info("=" * 60)
        logger.info(f"✓ User ingestion completed in {execution_time:.2f} seconds")
        logger.info(f"  Records ingested: {metadata['record_count']:,}")
        logger.info(f"  File size: {metadata['file_size_bytes']:,} bytes")
        logger.info(f"  Storage path: {metadata['file_path']}")
        logger.info("=" * 60)
        
        return metadata


def main():
    """Main execution function"""
    try:
        ingestion = UserDataIngestion()
        metadata = ingestion.ingest()
        
        print("\n✓ User data ingestion successful!")
        print(f"Records: {metadata['record_count']:,}")
        print(f"Location: {metadata['file_path']}")
        
        return 0
    
    except Exception as e:
        logger.critical(f"User ingestion failed: {str(e)}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
