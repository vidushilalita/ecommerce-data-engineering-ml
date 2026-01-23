"""
Feast Feature Store Setup

Simplified feature store using SQLite for local development.
Feast is complex to set up, so we're using a lightweight alternative
that mimics feature store functionality.
"""

import sys
import json
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.logger import get_logger
from src.utils.storage import DataLakeStorage

logger = get_logger(__name__)


class SimpleFeatureStore:
    """Lightweight feature store using SQLite"""
    
    def __init__(self, db_path: str = 'feature_store.db'):
        """Initialize feature store"""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        logger.info(f"Initialized SimpleFeatureStore at {db_path}")
        self._setup_tables()
    
    def _setup_tables(self):
        """Create feature store tables"""
        cursor = self.conn.cursor()
        
        # User features table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_features (
                user_id INTEGER PRIMARY KEY,
                user_activity_count INTEGER,
                avg_rating_given REAL,
                purchase_ratio REAL,
                preferred_category TEXT,
                age INTEGER,
                gender TEXT,
                device TEXT,
                gender_encoded INTEGER,
                device_encoded INTEGER,
                age_normalized REAL,
                updated_at TIMESTAMP
            )
        ''')
        
        # Item features table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS item_features (
                item_id INTEGER PRIMARY KEY,
                price REAL,
                brand TEXT,
                category TEXT,
                rating REAL,
                in_stock BOOLEAN,
                popularity_score INTEGER,
                avg_item_rating REAL,
                view_to_purchase_rate REAL,
                price_tier TEXT,
                category_encoded INTEGER,
                brand_encoded INTEGER,
                price_normalized REAL,
                updated_at TIMESTAMP
            )
        ''')
        
        # Feature metadata table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feature_metadata (
                feature_name TEXT PRIMARY KEY,
                feature_type TEXT,
                description TEXT,
                data_type TEXT,
                source_table TEXT,
                computation_logic TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        ''')
        
        self.conn.commit()
        logger.info("✓ Feature store tables created")
    
    def register_user_features(self, user_features_df: pd.DataFrame):
        """Register user features"""
        logger.info(f"Registering user features ({len(user_features_df)} records)...")
        
        # Add updated_at timestamp
        user_features_df['updated_at'] = datetime.now()
        
        # Save to database
        user_features_df.to_sql('user_features', self.conn, if_exists='replace', index=False)
        
        logger.info("✓ User features registered")
    
    def register_item_features(self, item_features_df: pd.DataFrame):
        """Register item features"""
        logger.info(f"Registering item features ({len(item_features_df)} records)...")
        
        # Add updated_at timestamp
        item_features_df['updated_at'] = datetime.now()
        
        # Save to database
        item_features_df.to_sql('item_features', self.conn, if_exists='replace', index=False)
        
        logger.info("✓ Item features registered")
    
    def register_feature_metadata(self, metadata: List[Dict]):
        """Register feature metadata"""
        logger.info(f"Registering {len(metadata)} feature definitions...")
        
        cursor = self.conn.cursor()
        
        for meta in metadata:
            cursor.execute('''
                INSERT OR REPLACE INTO feature_metadata 
                (feature_name, feature_type, description, data_type, source_table, computation_logic, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                meta['feature_name'],
                meta['feature_type'],
                meta['description'],
                meta['data_type'],
                meta['source_table'],
                meta['computation_logic'],
                datetime.now(),
                datetime.now()
            ))
        
        self.conn.commit()
        logger.info("✓ Feature metadata registered")
    
    def get_user_features(self, user_ids: Optional[List[int]] = None) -> pd.DataFrame:
        """Retrieve user features"""
        if user_ids is None:
            query = "SELECT * FROM user_features"
            df = pd.read_sql_query(query, self.conn)
        else:
            placeholders = ','.join('?' * len(user_ids))
            query = f"SELECT * FROM user_features WHERE user_id IN ({placeholders})"
            df = pd.read_sql_query(query, self.conn, params=user_ids)
        
        logger.info(f"Retrieved {len(df)} user feature records")
        return df
    
    def get_item_features(self, item_ids: Optional[List[int]] = None) -> pd.DataFrame:
        """Retrieve item features"""
        if item_ids is None:
            query = "SELECT * FROM item_features"
            df = pd.read_sql_query(query, self.conn)
        else:
            placeholders = ','.join('?' * len(item_ids))
            query = f"SELECT * FROM item_features WHERE item_id IN ({placeholders})"
            df = pd.read_sql_query(query, self.conn, params=item_ids)
        
        logger.info(f"Retrieved {len(df)} item feature records")
        return df
    
    def get_feature_metadata(self) -> pd.DataFrame:
        """Retrieve all feature metadata"""
        query = "SELECT * FROM feature_metadata"
        df = pd.read_sql_query(query, self.conn)
        return df
    
    def export_metadata(self, output_path: str):
        """Export feature metadata to JSON"""
        metadata_df = self.get_feature_metadata()
        metadata_dict = metadata_df.to_dict(orient='records')
        
        with open(output_path, 'w') as f:
            json.dump(metadata_dict, f, indent=2, default=str)
        
        logger.info(f"Exported feature metadata to {output_path}")
    
    def close(self):
        """Close database connection"""
        self.conn.close()
        logger.info("Feature store connection closed")


def create_feature_metadata() -> List[Dict]:
    """Define feature metadata"""
    metadata = [
        # User features
        {
            'feature_name': 'user_activity_count',
            'feature_type': 'user',
            'description': 'Total number of user interactions',
            'data_type': 'INTEGER',
            'source_table': 'transactions',
            'computation_logic': 'COUNT(transactions WHERE user_id = X)'
        },
        {
            'feature_name': 'avg_rating_given',
            'feature_type': 'user',
            'description': 'Average rating given by user',
            'data_type': 'REAL',
            'source_table': 'transactions',
            'computation_logic': 'AVG(rating WHERE user_id = X)'
        },
        {
            'feature_name': 'purchase_ratio',
            'feature_type': 'user',
            'description': 'Proportion of interactions that are purchases',
            'data_type': 'REAL',
            'source_table': 'transactions',
            'computation_logic': 'COUNT(purchases) / COUNT(total_interactions)'
        },
        # Item features
        {
            'feature_name': 'popularity_score',
            'feature_type': 'item',
            'description': 'Number of interactions the item received',
            'data_type': 'INTEGER',
            'source_table': 'transactions',
            'computation_logic': 'COUNT(interactions WHERE item_id = Y)'
        },
        {
            'feature_name': 'avg_item_rating',
            'feature_type': 'item',
            'description': 'Average rating received by item',
            'data_type': 'REAL',
            'source_table': 'transactions',
            'computation_logic': 'AVG(rating WHERE item_id = Y)'
        },
        {
            'feature_name': 'view_to_purchase_rate',
            'feature_type': 'item',
            'description': 'Conversion rate from views to purchases',
            'data_type': 'REAL',
            'source_table': 'transactions',
            'computation_logic': 'COUNT(purchases) / COUNT(views)'
        },
    ]
    
    return metadata


def main():
    """Setup feature store"""
    try:
        logger.info("=" * 60)
        logger.info("Setting up Feature Store")
        logger.info("=" * 60)
        
        # Load features from storage
        storage = DataLakeStorage()
        user_features = storage.load_latest('user_features', 'features')
        item_features = storage.load_latest('item_features', 'features')
        
        # Initialize feature store
        feature_store = SimpleFeatureStore()
        
        # Register features
        feature_store.register_user_features(user_features)
        feature_store.register_item_features(item_features)
        
        # Register metadata
        metadata = create_feature_metadata()
        feature_store.register_feature_metadata(metadata)
        
        # Export metadata
        docs_dir = Path('docs')
        docs_dir.mkdir(exist_ok=True)
        feature_store.export_metadata(str(docs_dir / 'feature_metadata.json'))
        
        # Demo retrieval
        logger.info("\nDemo: Retrieving features for sample users...")
        sample_users = user_features['user_id'].head(3).tolist()
        retrieved = feature_store.get_user_features(sample_users)
        logger.info(f"Retrieved {len(retrieved)} user records")
        
        feature_store.close()
        
        logger.info("=" * 60)
        logger.info("✓ Feature store setup complete")
        logger.info(f"  Database: feature_store.db")
        logger.info(f"  User features: {len(user_features)} records")
        logger.info(f"  Item features: {len(item_features)} records")
        logger.info("=" * 60)
        
        return 0
    
    except Exception as e:
        logger.critical(f"Feature store setup failed: {str(e)}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
