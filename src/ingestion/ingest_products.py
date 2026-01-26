"""
Product data ingestion module

Ingests product data from JSON file, flattens nested structures,
and stores in partitioned raw storage with metadata tracking.
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.logger import get_logger
from src.utils.storage import DataLakeStorage

logger = get_logger(__name__)

from src.config import config

class ProductDataIngestion:
    """Handles ingestion of product data from JSON source"""
    
    def __init__(self, data_dir: str = config['data_dir'], storage_base: str = config['storage_base']):
        """
        Initialize product data ingestion
        
        Args:
            data_dir: Directory containing source data files
            storage_base: Base directory for data lake storage
        """
        self.data_dir = Path(data_dir)
        self.storage = DataLakeStorage(storage_base)
        self.product_file = config['products_file']
        logger.info(f"Initialized ProductDataIngestion with data_dir={data_dir}")
    
    def validate_source_file(self) -> bool:
        """
        Validate that source file exists and is accessible
        
        Returns:
            True if file exists, raises exception otherwise
        """
        file_path = self.data_dir / self.product_file
        
        if not file_path.exists():
            logger.error(f"✗ Missing {self.product_file}")
            raise FileNotFoundError(f"Product file not found: {file_path}")
        
        file_size = os.path.getsize(file_path)
        logger.info(f" Found {self.product_file} ({file_size:,} bytes)")
        
        return True
    
    def read_product_json(self) -> List[Dict]:
        """
        Read product JSON file with error handling
        
        Returns:
            List of product dictionaries
        """
        file_path = self.data_dir / self.product_file
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                products = json.load(f)
            
            logger.info(f"Read {len(products)} products from JSON")
            return products
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format: {str(e)}")
            raise
        
        except Exception as e:
            logger.error(f"Error reading {self.product_file}: {str(e)}")
            raise
    
    def flatten_and_convert(self, products: List[Dict]) -> pd.DataFrame:
        """
        Flatten nested JSON structures and convert to DataFrame
        
        Args:
            products: List of product dictionaries
        
        Returns:
            Flattened DataFrame
        """
        logger.info("Flattening JSON structures...")
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame(products)
            
            logger.info(f"Created DataFrame with shape {df.shape}")
            logger.info(f"Columns: {df.columns.tolist()}")
            
            # Log data types
            logger.debug(f"Data types:\n{df.dtypes}")
            
            return df
        
        except Exception as e:
            logger.error(f"Error converting JSON to DataFrame: {str(e)}")
            raise
    
    def validate_product_data(self, df: pd.DataFrame) -> None:
        """
        Perform basic validation on product data
        
        Args:
            df: Product DataFrame to validate
        """
        logger.info("Validating product data structure...")
        
        # Expected columns
        expected_columns = {'item_id', 'price', 'brand', 'category', 'rating', 'in_stock'}
        missing_columns = expected_columns - set(df.columns)
        
        if missing_columns:
            logger.warning(f"Missing expected columns: {missing_columns}")
        
        # Check for nulls in critical columns
        critical_columns = ['item_id', 'price', 'category']
        for col in critical_columns:
            if col in df.columns:
                null_count = df[col].isnull().sum()
                if null_count > 0:
                    logger.warning(f"Found {null_count} null values in critical column '{col}'")
        
        # Check for unique item_ids
        if 'item_id' in df.columns:
            duplicate_ids = df.duplicated(subset=['item_id']).sum()
            if duplicate_ids > 0:
                logger.warning(f"Found {duplicate_ids} duplicate item_ids")
        
        logger.info(" Validation complete")
    
    def ingest(self) -> Dict[str, Any]:
        """
        Execute complete product data ingestion pipeline
        
        Returns:
            Metadata dictionary from storage operation
        """
        logger.info("=" * 60)
        logger.info("Starting Product Data Ingestion")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        # Step 1: Validate source file
        logger.info("Step 1: Validating source file...")
        self.validate_source_file()
        
        # Step 2: Read JSON data
        logger.info("Step 2: Reading product JSON...")
        products = self.read_product_json()
        
        # Step 3: Flatten and convert to DataFrame
        logger.info("Step 3: Converting to DataFrame...")
        df = self.flatten_and_convert(products)
        
        # Step 4: Validate data
        logger.info("Step 4: Validating product data...")
        self.validate_product_data(df)
        
        # Step 5: Store in data lake
        logger.info("Step 5: Storing in partitioned data lake...")
        metadata = self.storage.save_dataframe(
            df=df,
            source='products',
            data_type='raw',
            filename='products',
            format='parquet'
        )
        
        # Calculate execution time
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        logger.info("=" * 60)
        logger.info(f" Product ingestion completed in {execution_time:.2f} seconds")
        logger.info(f"  Records ingested: {metadata['record_count']:,}")
        logger.info(f"  File size: {metadata['file_size_bytes']:,} bytes")
        logger.info(f"  Storage path: {metadata['file_path']}")
        logger.info("=" * 60)
        
        return metadata


def main():
    """Main execution function"""
    try:
        ingestion = ProductDataIngestion()
        metadata = ingestion.ingest()
        
        print("\n Product data ingestion successful!")
        print(f"Records: {metadata['record_count']:,}")
        print(f"Location: {metadata['file_path']}")
        
        return 0
    
    except Exception as e:
        logger.critical(f"Product ingestion failed: {str(e)}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
