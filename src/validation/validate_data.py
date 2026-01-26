"""
Data validation module using Great Expectations

This module sets up and runs data validation for all datasets:
- Users: Schema validation, range checks, uniqueness
- Products: Required fields, price validation, rating ranges
- Transactions: Foreign key checks, interaction type validation
"""

import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.logger import get_logger
from src.utils.storage import DataLakeStorage

logger = get_logger(__name__)


class NumpyEncoder(json.JSONEncoder):
    """Custom encoder for NumPy types"""
    def default(self, obj):
        if isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        if isinstance(obj, (np.integer, int)):
            return int(obj)
        if isinstance(obj, (np.floating, float)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)


class DataValidator:
    """Data validation using pandas-based checks (Great Expectations alternative)"""
    
    def __init__(self, storage_base: str = 'storage'):
        """Initialize validator"""
        self.storage = DataLakeStorage(storage_base)
        self.validation_results = {}
        logger.info("Initialized DataValidator")
    
    def validate_users(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate user data"""
        logger.info("Validating user data...")
        
        results = {
            'dataset': 'users',
            'record_count': int(len(df)),
            'validations': [],
            'quality_score': 0.0
        }
        
        checks = []
        
        # Check 1: user_id uniqueness
        duplicate_ids = df.duplicated(subset=['user_id']).sum()
        checks.append({
            'check': 'user_id_unique',
            'passed': bool(duplicate_ids == 0),
            'details': f"{duplicate_ids} duplicates found"
        })
        
        # Check 2: age range (18-65)
        if 'age' in df.columns:
            age_in_range = df['age'].between(18, 65).sum()
            age_pass_rate = age_in_range / len(df)
            checks.append({
                'check': 'age_in_range_18_65',
                'passed': bool(age_pass_rate >= 0.95),
                'details': f"{age_pass_rate:.1%} within range"
            })
        
        # Check 3: gender values
        if 'gender' in df.columns:
            valid_genders = df['gender'].isin(['M', 'F', 'Male', 'Female']).sum()
            gender_pass_rate = valid_genders / len(df)
            checks.append({
                'check': 'gender_valid',
                'passed': bool(gender_pass_rate >= 0.95),
                'details': f"{gender_pass_rate:.1%} valid values"
            })
        
        # Check 4: device values
        if 'device' in df.columns:
            valid_devices = df['device'].isin(['Mobile', 'Desktop', 'Tablet']).sum()
            device_pass_rate = valid_devices / len(df)
            checks.append({
                'check': 'device_valid',
                'passed': bool(device_pass_rate >= 0.95),
                'details': f"{device_pass_rate:.1%} valid values"
            })
        
        # Check 5: Missing values
        null_counts = df.isnull().sum()
        critical_nulls = null_counts['user_id'] if 'user_id' in df.columns else 0
        checks.append({
            'check': 'no_null_user_ids',
            'passed': bool(critical_nulls == 0),
            'details': f"{critical_nulls} nulls in user_id"
        })
        
        results['validations'] = checks
        results['quality_score'] = sum(1 for c in checks if c['passed']) / len(checks)
        
        logger.info(f"User validation: {results['quality_score']:.1%} passed")
        return results
    
    def validate_products(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate product data"""
        logger.info("Validating product data...")
        
        results = {
            'dataset': 'products',
            'record_count': int(len(df)),
            'validations': [],
            'quality_score': 0.0
        }
        
        checks = []
        
        # Check 1: item_id uniqueness
        duplicate_ids = df.duplicated(subset=['item_id']).sum()
        checks.append({
            'check': 'item_id_unique',
            'passed': bool(duplicate_ids == 0),
            'details': f"{duplicate_ids} duplicates found"
        })
        
        # Check 2: price > 0
        if 'price' in df.columns:
            valid_prices = (df['price'] > 0).sum()
            price_pass_rate = valid_prices / len(df)
            checks.append({
                'check': 'price_positive',
                'passed': bool(price_pass_rate >= 0.99),
                'details': f"{price_pass_rate:.1%} positive prices"
            })
        
        # Check 3: rating in range 1.0-5.0
        if 'rating' in df.columns:
            valid_ratings = df['rating'].between(1.0, 5.0).sum()
            rating_pass_rate = valid_ratings / len(df)
            checks.append({
                'check': 'rating_in_range_1_5',
                'passed': bool(rating_pass_rate >= 0.95),
                'details': f"{rating_pass_rate:.1%} within range"
            })
        
        # Check 4: Required fields not null
        required_fields = ['item_id', 'price', 'category']
        for field in required_fields:
            if field in df.columns:
                null_count = df[field].isnull().sum()
                checks.append({
                    'check': f'{field}_not_null',
                    'passed': bool(null_count == 0),
                    'details': f"{null_count} nulls in {field}"
                })
        
        results['validations'] = checks
        results['quality_score'] = sum(1 for c in checks if c['passed']) / len(checks)
        
        logger.info(f"Product validation: {results['quality_score']:.1%} passed")
        return results
    
    def validate_transactions(self, df: pd.DataFrame, users_df: pd.DataFrame, products_df: pd.DataFrame) -> Dict[str, Any]:
        """Validate transaction data"""
        logger.info("Validating transaction data...")
        
        results = {
            'dataset': 'transactions',
            'record_count': int(len(df)),
            'validations': [],
            'quality_score': 0.0
        }
        
        checks = []
        
        # Check 1: Foreign key - user_id exists in users
        if 'user_id' in df.columns and 'user_id' in users_df.columns:
            valid_users = df['user_id'].isin(users_df['user_id']).sum()
            user_fk_rate = valid_users / len(df)
            checks.append({
                'check': 'user_id_foreign_key',
                'passed': bool(user_fk_rate >= 0.90),
                'details': f"{user_fk_rate:.1%} valid user references"
            })
        
        # Check 2: Foreign key - item_id exists in products
        if 'item_id' in df.columns and 'item_id' in products_df.columns:
            valid_items = df['item_id'].isin(products_df['item_id']).sum()
            item_fk_rate = valid_items / len(df)
            checks.append({
                'check': 'item_id_foreign_key',
                'passed': bool(item_fk_rate >= 0.90),
                'details': f"{item_fk_rate:.1%} valid item references"
            })
        
        # Check 3: view_mode valid
        if 'view_mode' in df.columns:
            valid_modes = df['view_mode'].isin(['view', 'add_to_cart', 'purchase']).sum()
            mode_pass_rate = valid_modes / len(df)
            checks.append({
                'check': 'view_mode_valid',
                'passed': bool(mode_pass_rate >= 0.99),
                'details': f"{mode_pass_rate:.1%} valid interaction types"
            })
        
        # Check 4: rating in range 1-5
        if 'rating' in df.columns:
            valid_ratings = df['rating'].between(1, 5).sum()
            rating_pass_rate = valid_ratings / len(df)
            checks.append({
                'check': 'rating_in_range_1_5',
                'passed': bool(rating_pass_rate >= 0.95),
                'details': f"{rating_pass_rate:.1%} within range"
            })
        
        # Check 5: timestamp validity
        if 'timestamp' in df.columns:
            valid_timestamps = pd.to_datetime(df['timestamp'], errors='coerce').notna().sum()
            timestamp_rate = valid_timestamps / len(df)
            checks.append({
                'check': 'timestamp_valid',
                'passed': bool(timestamp_rate >= 0.99),
                'details': f"{timestamp_rate:.1%} valid timestamps"
            })
        
        results['validations'] = checks
        results['quality_score'] = sum(1 for c in checks if c['passed']) / len(checks)
        
        logger.info(f"Transaction validation: {results['quality_score']:.1%} passed")
        return results
    
    def run_validation_suite(self) -> Dict[str, Any]:
        """Run complete validation suite"""
        logger.info("=" * 60)
        logger.info("Starting Data Validation Suite")
        logger.info("=" * 60)
        
        # Load datasets
        logger.info("Loading datasets from storage...")
        users_df = self.storage.load_latest('users', 'raw')
        products_df = self.storage.load_latest('products', 'raw')
        transactions_df = self.storage.load_latest('transactions', 'raw')
        
        # Run validations
        results = {
            'users': self.validate_users(users_df),
            'products': self.validate_products(products_df),
            'transactions': self.validate_transactions(transactions_df, users_df, products_df)
        }
        
        # Calculate overall quality score
        total_checks = sum(len(r['validations']) for r in results.values())
        passed_checks = sum(
            sum(1 for v in r['validations'] if v['passed']) 
            for r in results.values()
        )
        overall_score = passed_checks / total_checks if total_checks > 0 else 0.0
        
        results['overall'] = {
            'quality_score': overall_score,
            'total_checks': total_checks,
            'passed_checks': passed_checks,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info("=" * 60)
        logger.info(f" Overall Data Quality Score: {overall_score:.1%}")
        logger.info(f"  Passed: {passed_checks}/{total_checks} checks")
        logger.info("=" * 60)
        
        return results
    
    def save_validation_results(self, results: Dict[str, Any]) -> str:
        """Save validation results to JSON"""
        output_dir = Path('reports')
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / f"validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, cls=NumpyEncoder)
        
        logger.info(f"Saved validation results to {output_file}")
        return str(output_file)


def main():
    """Main execution"""
    try:
        validator = DataValidator()
        results = validator.run_validation_suite()
        output_file = validator.save_validation_results(results)
        
        print(f"\n Validation complete!")
        print(f"Overall Quality Score: {results['overall']['quality_score']:.1%}")
        print(f"Results saved to: {output_file}")
        
        return 0
    
    except Exception as e:
        logger.critical(f"Validation failed: {str(e)}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
