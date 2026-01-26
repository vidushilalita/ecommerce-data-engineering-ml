"""
Master Pipeline Script

Runs all data pipeline steps in sequence:
1. Data Ingestion
2. Data Validation
3. Data Preparation
4. Feature Engineering
5. Model Training
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from src.ingestion.run_all_ingestion import run_all_ingestion
from src.validation.validate_data import DataValidator
from src.preparation.clean_data import DataPreparation
from src.features.engineer_features import FeatureEngineer
from src.models.collaborative_filtering import CollaborativeFilteringModel
from src.utils.logger import get_logger
from src.utils.storage import DataLakeStorage

logger = get_logger(__name__)


def run_complete_pipeline():
    """Execute complete end-to-end pipeline"""
    logger.info("=" * 70)
    logger.info("RECOMART DATA PIPELINE - COMPLETE EXECUTION")
    logger.info("=" * 70)
    
    start_time = datetime.now()
    results = {}
    
    try:
        # Step 1: Data Ingestion
        logger.info("\n[STEP 1/5] DATA INGESTION")
        logger.info("=" * 70)
        success = run_all_ingestion()
        if not success:
            raise Exception("Data ingestion failed")
        results['ingestion'] = 'SUCCESS'
        
        # Step 2: Data Validation  
        logger.info("\n[STEP 2/5] DATA VALIDATION")
        logger.info("=" * 70)
        validator = DataValidator()
        validation_results = validator.run_validation_suite()
        validator.save_validation_results(validation_results)
        results['validation'] = f"Quality Score: {validation_results['overall']['quality_score']:.1%}"
        
        # Step 3: Data Preparation
        logger.info("\n[STEP 3/5] DATA PREPARATION")
        logger.info("=" * 70)
        prep = DataPreparation()
        users, products, transactions = prep.run_preparation_pipeline()
        results['preparation'] = f"{len(users)} users, {len(products)} products, {len(transactions)} transactions"
        
        # Step 4: Feature Engineering
        logger.info("\n[STEP 4/5] FEATURE ENGINEERING")
        logger.info("=" * 70)
        engineer = FeatureEngineer()
        user_features, item_features, interaction_features = engineer.run_feature_engineering()
        results['features'] = f"{len(user_features)} user, {len(item_features)} item, {len(interaction_features)} interaction"
        
        # Step 5: Model Training
        logger.info("\n[STEP 5/5] MODEL TRAINING")
        logger.info("=" * 70)
        storage = DataLakeStorage()
        interactions_df = storage.load_latest('interaction_features', 'features')
        
        cf_model = CollaborativeFilteringModel()
        dataset = cf_model.prepare_data(interactions_df)
        trainset, testset = cf_model.train(dataset)
        
        # Save model
        model_dir = Path('models')
        model_dir.mkdir(exist_ok=True)
        cf_model.save_model(str(model_dir / 'collaborative_filtering.pkl'))
        results['model'] = 'Collaborative Filtering trained'
        
        # Calculate total time
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds() / 60  # minutes
        
        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("PIPELINE EXECUTION SUMMARY")
        logger.info("=" * 70)
        for step, result in results.items():
            logger.info(f" {step.upper()}: {result}")
        logger.info(f"\nTotal execution time: {total_time:.2f} minutes")
        logger.info("=" * 70)
        
        return True
        
    except Exception as e:
        logger.critical(f"Pipeline failed: {str(e)}", exc_info=True)
        return False


def main():
    """Main execution"""
    success = run_complete_pipeline()
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
