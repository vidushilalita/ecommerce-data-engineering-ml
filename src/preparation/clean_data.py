"""
Data Preparation and Cleaning Module

Performs data cleaning, preprocessing, and normalization:
- Handle missing values
- Encode categorical attributes
- Normalize numerical variables
- Remove duplicates and invalid records
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple
from sklearn.preprocessing import LabelEncoder, MinMaxScaler

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.logger import get_logger
from src.utils.storage import DataLakeStorage

logger = get_logger(__name__)


class DataPreparation:
    """Data cleaning and preparation pipeline"""
    
    def __init__(self, storage_base: str = 'storage'):
        """Initialize data preparation"""
        self.storage = DataLakeStorage(storage_base)
        self.encoders = {}
        self.scalers = {}
        logger.info("Initialized DataPreparation")
    
    def clean_users(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean user data"""
        logger.info(f"Cleaning user data ({len(df)} records)...")
        
        df_clean = df.copy()
        
        # Remove duplicates
        initial_count = len(df_clean)
        df_clean = df_clean.drop_duplicates(subset=['user_id'], keep='first')
        logger.info(f"  Removed {initial_count - len(df_clean)} duplicate user_ids")
        
        # Handle missing values
        if 'age' in df_clean.columns:
            median_age = df_clean['age'].median()
            missing_age = df_clean['age'].isnull().sum()
            if missing_age > 0:
                df_clean['age'].fillna(median_age, inplace=True)
                logger.info(f"  Filled {missing_age} missing ages with median ({median_age})")
        
        if 'gender' in df_clean.columns:
            mode_gender = df_clean['gender'].mode()[0] if not df_clean['gender'].mode().empty else 'M'
            missing_gender = df_clean['gender'].isnull().sum()
            if missing_gender > 0:
                df_clean['gender'].fillna(mode_gender, inplace=True)
                logger.info(f"  Filled {missing_gender} missing genders with mode ({mode_gender})")
        
        if 'device' in df_clean.columns:
            mode_device = df_clean['device'].mode()[0] if not df_clean['device'].mode().empty else 'Mobile'
            missing_device = df_clean['device'].isnull().sum()
            if missing_device > 0:
                df_clean['device'].fillna(mode_device, inplace=True)
                logger.info(f"  Filled {missing_device} missing devices with mode ({mode_device})")
        
        # Encode categorical variables
        if 'gender' in df_clean.columns:
            gender_encoder = LabelEncoder()
            df_clean['gender_encoded'] = gender_encoder.fit_transform(df_clean['gender'].astype(str))
            self.encoders['gender'] = gender_encoder
            logger.info(f"  Encoded gender: {dict(zip(gender_encoder.classes_, gender_encoder.transform(gender_encoder.classes_)))}")
        
        if 'device' in df_clean.columns:
            device_encoder = LabelEncoder()
            df_clean['device_encoded'] = device_encoder.fit_transform(df_clean['device'].astype(str))
            self.encoders['device'] = device_encoder
            logger.info(f"  Encoded device: {dict(zip(device_encoder.classes_, device_encoder.transform(device_encoder.classes_)))}")
        
        # Normalize age
        if 'age' in df_clean.columns:
            age_scaler = MinMaxScaler()
            df_clean['age_normalized'] = age_scaler.fit_transform(df_clean[['age']])
            self.scalers['age'] = age_scaler
            logger.info(f"  Normalized age to [0, 1] range")
        
        logger.info(f" User data cleaned: {len(df_clean)} records")
        return df_clean
    
    def clean_products(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean product data"""
        logger.info(f"Cleaning product data ({len(df)} records)...")
        
        df_clean = df.copy()
        
        # Remove duplicates
        initial_count = len(df_clean)
        df_clean = df_clean.drop_duplicates(subset=['item_id'], keep='first')
        logger.info(f"  Removed {initial_count - len(df_clean)} duplicate item_ids")
        
        # Handle missing prices
        if 'price' in df_clean.columns:
            missing_price = df_clean['price'].isnull().sum()
            if missing_price > 0:
                median_price = df_clean.groupby('category')['price'].transform('median')
                df_clean['price'].fillna(median_price, inplace=True)
                logger.info(f"  Filled {missing_price} missing prices with category median")
        
        # Handle missing ratings
        if 'rating' in df_clean.columns:
            mean_rating = df_clean['rating'].mean()
            missing_rating = df_clean['rating'].isnull().sum()
            if missing_rating > 0:
                df_clean['rating'].fillna(mean_rating, inplace=True)
                logger.info(f"  Filled {missing_rating} missing ratings with mean ({mean_rating:.2f})")
        
        # Encode categorical variables
        if 'category' in df_clean.columns:
            category_encoder = LabelEncoder()
            df_clean['category_encoded'] = category_encoder.fit_transform(df_clean['category'].astype(str))
            self.encoders['category'] = category_encoder
            logger.info(f"  Encoded {len(category_encoder.classes_)} categories")
        
        if 'brand' in df_clean.columns:
            brand_encoder = LabelEncoder()
            df_clean['brand_encoded'] = brand_encoder.fit_transform(df_clean['brand'].astype(str))
            self.encoders['brand'] = brand_encoder
            logger.info(f"  Encoded {len(brand_encoder.classes_)} brands")
        
        # Normalize price
        if 'price' in df_clean.columns:
            price_scaler = MinMaxScaler()
            df_clean['price_normalized'] = price_scaler.fit_transform(df_clean[['price']])
            self.scalers['price'] = price_scaler
            logger.info(f"  Normalized price to [0, 1] range")
        
        # Create price tiers
        if 'price' in df_clean.columns:
            df_clean['price_tier'] = pd.qcut(df_clean['price'], q=3, labels=['low', 'medium', 'high'], duplicates='drop')
            logger.info(f"  Created price tiers: {df_clean['price_tier'].value_counts().to_dict()}")
        
        logger.info(f" Product data cleaned: {len(df_clean)} records")
        return df_clean
    
    def clean_transactions(self, df: pd.DataFrame, users_df: pd.DataFrame, products_df: pd.DataFrame) -> pd.DataFrame:
        """Clean transaction data"""
        logger.info(f"Cleaning transaction data ({len(df)} records)...")
        
        df_clean = df.copy()
        initial_count = len(df_clean)
        
        # Remove transactions with invalid user_ids
        valid_user_ids = set(users_df['user_id'].unique())
        df_clean = df_clean[df_clean['user_id'].isin(valid_user_ids)]
        logger.info(f"  Removed {initial_count - len(df_clean)} transactions with invalid user_ids")
        
        # Remove transactions with invalid item_ids
        initial_count = len(df_clean)
        valid_item_ids = set(products_df['item_id'].unique())
        df_clean = df_clean[df_clean['item_id'].isin(valid_item_ids)]
        logger.info(f"  Removed {initial_count - len(df_clean)} transactions with invalid item_ids")
        
        # Parse timestamps
        if 'timestamp' in df_clean.columns:
            df_clean['timestamp'] = pd.to_datetime(df_clean['timestamp'], errors='coerce')
            invalid_timestamps = df_clean['timestamp'].isnull().sum()
            if invalid_timestamps > 0:
                df_clean = df_clean.dropna(subset=['timestamp'])
                logger.info(f"  Removed {invalid_timestamps} records with invalid timestamps")
        
        # Encode view_mode
        if 'view_mode' in df_clean.columns:
            view_mode_encoder = LabelEncoder()
            df_clean['view_mode_encoded'] = view_mode_encoder.fit_transform(df_clean['view_mode'].astype(str))
            self.encoders['view_mode'] = view_mode_encoder
            logger.info(f"  Encoded view_mode: {dict(zip(view_mode_encoder.classes_, view_mode_encoder.transform(view_mode_encoder.classes_)))}")
        
        # Create implicit scores (view=1, add_to_cart=2, purchase=3)
        if 'view_mode' in df_clean.columns:
            view_mode_scores = {'view': 1, 'add_to_cart': 2, 'purchase': 3}
            df_clean['implicit_score'] = df_clean['view_mode'].map(view_mode_scores)
            logger.info(f"  Created implicit scores: {df_clean['implicit_score'].value_counts().to_dict()}")
        
        logger.info(f" Transaction data cleaned: {len(df_clean)} records")
        return df_clean
    
    def run_preparation_pipeline(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Run complete data preparation pipeline"""
        logger.info("=" * 60)
        logger.info("Starting Data Preparation Pipeline")
        logger.info("=" * 60)
        
        # Load raw data
        logger.info("Loading raw datasets...")
        users_df = self.storage.load_latest('users', 'raw')
        products_df = self.storage.load_latest('products', 'raw')
        transactions_df = self.storage.load_latest('transactions', 'raw')
        
        # Clean data
        users_clean = self.clean_users(users_df)
        products_clean = self.clean_products(products_df)
        transactions_clean = self.clean_transactions(transactions_df, users_clean, products_clean)
        
        # Save cleaned data
        logger.info("\nSaving cleaned datasets...")
        self.storage.save_dataframe(users_clean, 'users', 'prepared', 'users_clean')
        self.storage.save_dataframe(products_clean, 'products', 'prepared', 'products_clean')
        self.storage.save_dataframe(transactions_clean, 'transactions', 'prepared', 'transactions_clean')
        
        logger.info("=" * 60)
        logger.info(" Data preparation complete")
        logger.info("=" * 60)
        
        return users_clean, products_clean, transactions_clean


def main():
    """Main execution"""
    try:
        prep = DataPreparation()
        users, products, transactions = prep.run_preparation_pipeline()
        
        print(f"\n Data preparation successful!")
        print(f"Users: {len(users):,} records")
        print(f"Products: {len(products):,} records")
        print(f"Transactions: {len(transactions):,} records")
        
        return 0
    
    except Exception as e:
        logger.critical(f"Data preparation failed: {str(e)}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
