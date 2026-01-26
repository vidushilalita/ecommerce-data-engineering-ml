"""
Feature Engineering Module

Creates features for recommendation system:
- User features: activity count, avg rating, purchase ratio, preferred category
- Item features: popularity score, avg rating, price tier, view-to-purchase rate
- Interaction features: implicit scores, recency weights
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.logger import get_logger
from src.utils.storage import DataLakeStorage

logger = get_logger(__name__)


class FeatureEngineer:
    """Feature engineering for recommendation system"""
    
    def __init__(self, storage_base: str = 'storage'):
        """Initialize feature engineer"""
        self.storage = DataLakeStorage(storage_base)
        logger.info("Initialized FeatureEngineer")
    
    def create_user_features(self, transactions_df: pd.DataFrame, users_df: pd.DataFrame, products_df: pd.DataFrame) -> pd.DataFrame:
        """Create user-level features"""
        logger.info("Creating user features...")
        
        # Merge transactions with products to get categories
        trans_with_products = transactions_df.merge(
            products_df[['item_id', 'category']], 
            on='item_id',
            how='left'
        )
        
        # Group by user
        user_features = []
        
        for user_id in users_df['user_id'].unique():
            user_trans = trans_with_products[trans_with_products['user_id'] == user_id]
            
            if len(user_trans) == 0:
                features = {
                    'user_id': user_id,
                    'user_activity_count': 0,
                    'avg_rating_given': 0.0,
                    'purchase_ratio': 0.0,
                    'preferred_category': 'Unknown'
                }
            else:
                # Activity count
                activity_count = len(user_trans)
                
                # Average rating given
                avg_rating = user_trans['rating'].mean() if 'rating' in user_trans.columns else 0.0
                
                # Purchase ratio
                if 'view_mode' in user_trans.columns:
                    purchases = (user_trans['view_mode'] == 'purchase').sum()
                    purchase_ratio = purchases / len(user_trans) if len(user_trans) > 0 else 0.0
                else:
                    purchase_ratio = 0.0
                
                # Preferred category
                if 'category' in user_trans.columns and not user_trans['category'].isnull().all():
                    preferred_cat = user_trans['category'].mode()[0] if not user_trans['category'].mode().empty else 'Unknown'
                else:
                    preferred_cat = 'Unknown'
                
                features = {
                    'user_id': user_id,
                    'user_activity_count': activity_count,
                    'avg_rating_given': avg_rating,
                    'purchase_ratio': purchase_ratio,
                    'preferred_category': preferred_cat
                }
            
            user_features.append(features)
        
        user_features_df = pd.DataFrame(user_features)
        
        # Merge with user demographics
        user_features_df = user_features_df.merge(users_df, on='user_id', how='left')
        
        logger.info(f" Created {len(user_features_df)} user feature records")
        return user_features_df
    
    def create_item_features(self, transactions_df: pd.DataFrame, products_df: pd.DataFrame) -> pd.DataFrame:
        """Create item-level features"""
        logger.info("Creating item features...")
        
        # Group by item
        item_stats = transactions_df.groupby('item_id').agg({
            'user_id': 'count',  # popularity
            'rating': 'mean',     # avg rating
            'view_mode': lambda x: (x == 'purchase').sum() if 'view_mode' in transactions_df.columns else 0
        }).reset_index()
        
        item_stats.columns = ['item_id', 'popularity_score', 'avg_item_rating', 'purchase_count']
        
        # Calculate view count
        if 'view_mode' in transactions_df.columns:
            view_counts = transactions_df[transactions_df['view_mode'] == 'view'].groupby('item_id').size().reset_index(name='view_count')
            item_stats = item_stats.merge(view_counts, on='item_id', how='left')
            item_stats['view_count'].fillna(0, inplace=True)
            
            # View to purchase rate
            item_stats['view_to_purchase_rate'] = np.where(
                item_stats['view_count'] > 0,
                item_stats['purchase_count'] / item_stats['view_count'],
                0.0
            )
        else:
            item_stats['view_to_purchase_rate'] = 0.0
        
        # Merge with product metadata
        item_features_df = products_df.merge(item_stats, on='item_id', how='left')
        
        # Fill NaN for items with no transactions
        item_features_df['popularity_score'].fillna(0, inplace=True)
        item_features_df['avg_item_rating'].fillna(0, inplace=True)
        item_features_df['view_to_purchase_rate'].fillna(0, inplace=True)
        
        logger.info(f" Created {len(item_features_df)} item feature records")
        return item_features_df
    
    def create_interaction_features(self, transactions_df: pd.DataFrame) -> pd.DataFrame:
        """Create interaction-level features"""
        logger.info("Creating interaction features...")
        
        interactions_df = transactions_df.copy()
        
        # Implicit score (already created in clean_data, but verify)
        if 'implicit_score' not in interactions_df.columns and 'view_mode' in interactions_df.columns:
            view_mode_scores = {'view': 1, 'add_to_cart': 2, 'purchase': 3}
            interactions_df['implicit_score'] = interactions_df['view_mode'].map(view_mode_scores)
        
        # Recency weight (exponential decay)
        if 'timestamp' in interactions_df.columns:
            interactions_df['timestamp'] = pd.to_datetime(interactions_df['timestamp'])
            max_time = interactions_df['timestamp'].max()
            
            # Days since interaction
            interactions_df['days_since'] = (max_time - interactions_df['timestamp']).dt.days
            
            # Exponential decay with half-life of 30 days
            interactions_df['recency_weight'] = np.exp(-interactions_df['days_since'] / 30.0)
        else:
            interactions_df['recency_weight'] = 1.0
        
        # Combined affinity score
        if 'rating' in interactions_df.columns:
            # Normalize rating to 0-1
            interactions_df['rating_normalized'] = (interactions_df['rating'] - 1) / 4.0
            
            # Combined score: (implicit * 0.3) + (rating_norm * 0.5) + (recency * 0.2)
            interactions_df['user_item_affinity'] = (
                interactions_df['implicit_score'] / 3.0 * 0.3 +
                interactions_df['rating_normalized'] * 0.5 +
                interactions_df['recency_weight'] * 0.2
            )
        else:
            interactions_df['user_item_affinity'] = interactions_df['implicit_score'] / 3.0
        
        logger.info(f" Created {len(interactions_df)} interaction feature records")
        return interactions_df
    
    def run_feature_engineering(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Run complete feature engineering pipeline"""
        logger.info("=" * 60)
        logger.info("Starting Feature Engineering Pipeline")
        logger.info("=" * 60)
        
        # Load prepared data
        logger.info("Loading prepared datasets...")
        users_df = self.storage.load_latest('users', 'prepared')
        products_df = self.storage.load_latest('products', 'prepared')
        transactions_df = self.storage.load_latest('transactions', 'prepared')
        
        # Create features
        user_features = self.create_user_features(transactions_df, users_df, products_df)
        item_features = self.create_item_features(transactions_df, products_df)
        interaction_features = self.create_interaction_features(transactions_df)
        
        # Save features
        logger.info("\nSaving feature datasets...")
        self.storage.save_dataframe(user_features, 'user_features', 'features', 'user_features')
        self.storage.save_dataframe(item_features, 'item_features', 'features', 'item_features')
        self.storage.save_dataframe(interaction_features, 'interaction_features', 'features', 'interaction_features')
        
        logger.info("=" * 60)
        logger.info(" Feature engineering complete")
        logger.info("=" * 60)
        
        return user_features, item_features, interaction_features


def main():
    """Main execution"""
    try:
        engineer = FeatureEngineer()
        user_features, item_features, interaction_features = engineer.run_feature_engineering()
        
        print(f"\n Feature engineering successful!")
        print(f"User features: {len(user_features):,} records")
        print(f"Item features: {len(item_features):,} records")
        print(f"Interaction features: {len(interaction_features):,} records")
        
        return 0
    
    except Exception as e:
        logger.critical(f"Feature engineering failed: {str(e)}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
