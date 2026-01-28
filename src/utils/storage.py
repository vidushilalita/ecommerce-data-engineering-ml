"""
Storage utility module for RecoMart Data Pipeline

Provides functions for:
- Partitioned data storage in data lake structure
- Metadata generation and tracking
- File operations with error handling
- Data format conversions (CSV/JSON to Parquet)
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd
from pathlib import Path

from ..utils.logger import get_logger

logger = get_logger(__name__)


class DataLakeStorage:
    """Manages data lake storage with partitioning and metadata"""
    
    def __init__(self, base_path: str = 'storage'):
        """
        Initialize storage manager
        
        Args:
            base_path: Base directory for data lake
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized DataLakeStorage at {self.base_path}")
    
    def generate_partition_path(
        self,
        source: str,
        data_type: str,
        timestamp: Optional[datetime] = None
    ) -> Path:
        """
        Generate partitioned storage path
        
        Args:
            source: Data source name (e.g., 'users', 'products')
            data_type: Data layer (e.g., 'raw', 'validated', 'prepared')
            timestamp: Optional timestamp for partitioning (defaults to now)
        
        Returns:
            Path object for storage location
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Format: storage/{data_type}/{source}/{YYYY-MM-DD}/
        partition_path = self.base_path / data_type / source / timestamp.strftime('%Y-%m-%d')
        partition_path.mkdir(parents=True, exist_ok=True)
        
        logger.debug(f"Generated partition path: {partition_path}")
        return partition_path
    
    def save_dataframe(
        self,
        df: pd.DataFrame,
        source: str,
        data_type: str,
        filename: str,
        format: str = 'parquet',
        **kwargs
    ) -> Dict[str, Any]:
        """
        Save dataframe to partitioned storage
        
        Args:
            df: DataFrame to save
            source: Data source name
            data_type: Data layer
            filename: Output filename (without extension)
            format: File format ('parquet', 'csv', 'json')
            **kwargs: Additional arguments for pandas save methods
        
        Returns:
            Metadata dictionary with storage info
        """
        timestamp = datetime.now()
        partition_path = self.generate_partition_path(source, data_type, timestamp)
        
        # Add appropriate extension
        file_path = partition_path / f"{filename}.{format}"
        
        # Save based on format
        if format == 'parquet':
            df.to_parquet(file_path, index=False, **kwargs)
        elif format == 'csv':
            df.to_csv(file_path, index=False, **kwargs)
        elif format == 'json':
            df.to_json(file_path, orient='records', **kwargs)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        # Generate metadata
        metadata = self._generate_metadata(df, file_path, source, data_type, timestamp)
        
        # Save metadata
        metadata_path = partition_path / f"{filename}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        logger.info(f"Saved {len(df)} records to {file_path}")
        logger.info(f"Metadata saved to {metadata_path}")
        
        return metadata
    
    def _generate_metadata(
        self,
        df: pd.DataFrame,
        file_path: Path,
        source: str,
        data_type: str,
        timestamp: datetime
    ) -> Dict[str, Any]:
        """Generate metadata for stored data"""
        
        # Calculate file checksum
        checksum = self._calculate_checksum(file_path)
        
        metadata = {
            'source': source,
            'data_type': data_type,
            'timestamp': timestamp.isoformat(),
            'file_path': str(file_path),
            'file_size_bytes': os.path.getsize(file_path),
            'record_count': len(df),
            'schema': {
                'columns': df.columns.tolist(),
                'dtypes': df.dtypes.astype(str).to_dict()
            },
            'checksum_md5': checksum,
            'null_counts': df.isnull().sum().to_dict(),
            'memory_usage_bytes': df.memory_usage(deep=True).sum()
        }
        
        return metadata
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of file"""
        hash_md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def load_latest(
        self,
        source: str,
        data_type: str,
        format: str = 'parquet'
    ) -> pd.DataFrame:
        """
        Load most recent data from storage
        
        Args:
            source: Data source name
            data_type: Data layer
            format: File format
        
        Returns:
            DataFrame with loaded data
        """
        source_path = self.base_path / data_type / source
        
        if not source_path.exists():
            raise FileNotFoundError(f"No data found at {source_path}")
        
        # Find most recent partition
        partitions = sorted([p for p in source_path.iterdir() if p.is_dir()], reverse=True)
        
        if not partitions:
            raise FileNotFoundError(f"No partitions found in {source_path}")
        
        latest_partition = partitions[0]
        
        # Find data file
        data_files = list(latest_partition.glob(f"*.{format}"))
        data_files = [f for f in data_files if not f.stem.endswith('_metadata')]
        
        if not data_files:
            raise FileNotFoundError(f"No {format} files found in {latest_partition}")
        
        file_path = data_files[0]
        
        # Load based on format
        if format == 'parquet':
            df = pd.read_parquet(file_path)
        elif format == 'csv':
            df = pd.read_csv(file_path)
        elif format == 'json':
            df = pd.read_json(file_path)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"Loaded {len(df)} records from {file_path}")
        return df



def load_training(
        self,
        source: str,
        data_type: str,
        format: str = 'parquet'
    ) -> pd.DataFrame:
        """
        Load most recent data from storage
        
        Args:
            source: Data source name
            data_type: Data layer
            format: File format
        
        Returns:
            DataFrame with loaded data
        """
        source_path = self.base_path / data_type / source
        
        if not source_path.exists():
            raise FileNotFoundError(f"No data found at {source_path}")
        
        # Find most recent partition
        partitions = sorted([p for p in source_path.iterdir() if p.is_dir()], reverse=True)
        
        if not partitions:
            raise FileNotFoundError(f"No partitions found in {source_path}")
        
        latest_partition = partitions[0]
        df=pd.DataFrame()

        for p in partitions:
            data_files = list(p.glob(f"*.{format}"))
            file_path = data_files[0]
            data_files = [f for f in data_files if not f.stem.endswith('_metadata')]
            df_partition = pd.read_parquet(data_files[0])
            df=pd.concat([df,df_partition],ignore_index=True)
            logger.info(f"Loaded {len(df)} records from {file_path}")
        # Find data file
        #data_files = list(latest_partition.glob(f"*.{format}"))
        #data_files = [f for f in data_files if not f.stem.endswith('_metadata')]
        
        if not data_files:
            raise FileNotFoundError(f"No {format} files found in {latest_partition}")
        
        #file_path = data_files[0]
        
        return df




if __name__ == '__main__':
    # Test storage functionality
    storage = DataLakeStorage()
    
    # Create test dataframe
    test_df = pd.DataFrame({
        'id': [1, 2, 3],
        'name': ['Alice', 'Bob', 'Charlie'],
        'value': [100, 200, 300]
    })
    
    # Save test data
    metadata = storage.save_dataframe(
        test_df,
        source='test',
        data_type='raw',
        filename='test_data'
    )
    
    print("Metadata:", json.dumps(metadata, indent=2, default=str))
    
    # Load test data
    loaded_df = storage.load_latest('test', 'raw')
    print("\nLoaded data:")
    print(loaded_df)
