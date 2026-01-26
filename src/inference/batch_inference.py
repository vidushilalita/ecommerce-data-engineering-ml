"""
Batch Inference Module

Generates daily recommendations for all active users using the trained model.
Reads user/item features from Data Lake, loads the latest model, and 
stores top-k recommendations back to the Data Lake/Warehouse.
"""

import sys
import pandas as pd
from pathlib import Path
from typing import List, Dict
import json
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.models.collaborative_filtering import CollaborativeFilteringModel
from src.utils.logger import get_logger
from src.utils.storage import DataLakeStorage
from src.config import config

logger = get_logger(__name__)

class BatchInference:
    """Handles daily batch inference for all users"""
    
    def __init__(self):
        self.storage = DataLakeStorage()
        self.output_dir = Path(config.get('data_dir', 'data')) / 'recommendations'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def run_inference(self, top_k: int = 10) -> Dict[str, any]:
        """
        Run batch inference pipeline
        
        Args:
            top_k: Number of recommendations per user
            
        Returns:
            Metadata about the inference run
        """
        logger.info("=" * 60)
        logger.info("Starting Batch Inference Job")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        # 1. Load Data
        logger.info("Loading features and model...")
        interactions_df = self.storage.load_latest('interaction_features', 'features')
        
        # Get all users and items
        all_users = interactions_df['user_id'].unique().tolist()
        all_items = interactions_df['item_id'].unique().tolist()
        
        logger.info(f"Found {len(all_users)} users and {len(all_items)} items")
        
        # 2. Load Model
        # In a real scenario, we might track model versions better.
        # Here we assume the latest 'collaborative_filtering.pkl' is the one to use.
        model_path = Path('models/collaborative_filtering.pkl')
        if not model_path.exists():
            raise FileNotFoundError("Trained model not found. Run model training first.")
            
        model = CollaborativeFilteringModel()
        model.load_model(str(model_path))
        
        # 3. Generate Recommendations
        logger.info(f"Generating top-{top_k} recommendations for {len(all_users)} users...")
        
        all_recommendations = []
        
        for i, user_id in enumerate(all_users):
            if i % 100 == 0:
                logger.info(f"Proccessed {i}/{len(all_users)} users...")
            
            # Get items user has already interacted with to exclude them
            user_interacted = interactions_df[interactions_df['user_id'] == user_id]['item_id'].tolist()
            
            recs = model.generate_recommendations(
                user_id=user_id,
                all_item_ids=all_items,
                exclude_items=user_interacted,
                top_k=top_k
            )
            all_recommendations.extend(recs)
            
        # 4. Save Results
        logger.info("Saving recommendations...")
        
        # Convert to DataFrame
        recs_df = pd.DataFrame(all_recommendations)
        
        # Add timestamp
        recs_df['inference_date'] = datetime.now().isoformat()
        
        # Save to Data Lake (Partitioned by date would be ideal in prod)
        metadata = self.storage.save_dataframe(
            df=recs_df,
            source='inference',
            data_type='processed',
            filename=f'recommendations_{start_time.strftime("%Y%m%d")}',
            format='parquet'
        )
        
        # Also save a human-readable JSON sample for quick verification
        sample_file = self.output_dir / 'latest_recommendations_sample.json'
        sample_recs = recs_df.head(20).to_dict(orient='records')
        with open(sample_file, 'w') as f:
            json.dump(sample_recs, f, indent=2)
            
        execution_time = (datetime.now() - start_time).total_seconds()
        
        logger.info("=" * 60)
        logger.info(f"Inference completed in {execution_time:.2f} seconds")
        logger.info(f"Generated {len(recs_df)} recommendations")
        logger.info("=" * 60)
        
        return metadata

def main():
    try:
        inference = BatchInference()
        inference.run_inference()
        return 0
    except Exception as e:
        logger.critical(f"Batch inference failed: {str(e)}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())
