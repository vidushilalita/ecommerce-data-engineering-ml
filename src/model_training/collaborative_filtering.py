"""
Collaborative Filtering Model using Matrix Factorization (SVD)

Implements collaborative filtering for user-item recommendations
using Singular Value Decomposition (SVD) from the Surprise library.
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import pickle

from surprise import SVD, Dataset, Reader
from surprise.model_selection import train_test_split

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.logger import get_logger
from src.utils.storage import DataLakeStorage

logger = get_logger(__name__)


class CollaborativeFilteringModel:
    """Collaborative filtering recommendation model using SVD"""
    
    def __init__(self, n_factors: int = 50, n_epochs: int = 20, lr_all: float = 0.005, reg_all: float = 0.02):
        """
        Initialize CF model
        
        Args:
            n_factors: Number of latent factors
            n_epochs: Number of training epochs
            lr_all: Learning rate
            reg_all: Regularization parameter
        """
        self.model = SVD(
            n_factors=n_factors,
            n_epochs=n_epochs,
            lr_all=lr_all,
            reg_all=reg_all,
            random_state=42
        )
        self.storage = DataLakeStorage()
        self.trained = False
        logger.info(f"Initialized SVD model with {n_factors} factors, {n_epochs} epochs")
    
    def prepare_data(self, interactions_df: pd.DataFrame) -> Dataset:
        """Prepare data for Surprise library"""
        logger.info("Preparing data for collaborative filtering...")
        
        # Create rating matrix (user_id, item_id, affinity_score)
        if 'user_item_affinity' in interactions_df.columns:
            data = interactions_df[['user_id', 'item_id', 'user_item_affinity']].copy()
            # Scale affinity to 1-5 range for CFLogger
            data['user_item_affinity'] = data['user_item_affinity'] * 4 + 1
        elif 'rating' in interactions_df.columns:
            data = interactions_df[['user_id', 'item_id', 'rating']].copy()
            data.columns = ['user_id', 'item_id', 'user_item_affinity']
        else:
            logger.warning("No rating or affinity column found, using implicit_score")
            data = interactions_df[['user_id', 'item_id', 'implicit_score']].copy()
            data.columns = ['user_id', 'item_id', 'user_item_affinity']
        
        # Remove duplicates (keep highest rating)
        data = data.sort_values('user_item_affinity', ascending=False)
        data = data.drop_duplicates(subset=['user_id', 'item_id'], keep='first')
        
        logger.info(f"Prepared {len(data)} user-item interactions")
        
        # Create Surprise dataset
        reader = Reader(rating_scale=(1, 5))
        dataset = Dataset.load_from_df(data, reader)
        
        return dataset
    
    def train(self, dataset: Dataset, test_size: float = 0.2) -> Tuple[any, any]:
        """Train the model"""
        logger.info("Training collaborative filtering model...")
        
        # Split train/test
        trainset, testset = train_test_split(dataset, test_size=test_size, random_state=42)
        
        logger.info(f"Training set: {trainset.n_ratings} ratings")
        logger.info(f"Test set: {len(testset)} ratings")
        
        # Train
        self.model.fit(trainset)
        self.trained = True
        
        logger.info(" Model training complete")
        
        return trainset, testset
    
    def predict_for_user(self, user_id: int, item_ids: List[int], top_k: int = 10) -> List[Tuple[int, float]]:
        """Generate top-K recommendations for a user"""
        if not self.trained:
            raise ValueError("Model must be trained before making predictions")
        
        predictions = []
        for item_id in item_ids:
            pred = self.model.predict(user_id, item_id)
            predictions.append((item_id, pred.est))
        
        # Sort by predicted rating
        predictions.sort(key=lambda x: x[1], reverse=True)
        
        return predictions[:top_k]
    
    def generate_recommendations(self, user_id: int, all_item_ids: List[int], exclude_items: List[int] = None, top_k: int = 10) -> List[Dict]:
        """Generate recommendations excluding already interacted items"""
        if exclude_items is None:
            exclude_items = []
        
        # Filter out already interacted items
        candidate_items = [item_id for item_id in all_item_ids if item_id not in exclude_items]
        
        # Get predictions
        top_items = self.predict_for_user(user_id, candidate_items, top_k)
        
        # Format results
        recommendations = [
            {
                'user_id': user_id,
                'item_id': item_id,
                'predicted_score': float(score),
                'rank': rank + 1
            }
            for rank, (item_id, score) in enumerate(top_items)
        ]
        
        return recommendations
    
    def save_model(self, filepath: str):
        """Save trained model"""
        with open(filepath, 'wb') as f:
            pickle.dump(self.model, f)
        logger.info(f"Saved model to {filepath}")
    
    def load_model(self, filepath: str):
        """Load trained model"""
        with open(filepath, 'rb') as f:
            self.model = pickle.load(f)
        self.trained = True
        logger.info(f"Loaded model from {filepath}")


def main():
    """Main execution"""
    try:
        logger.info("=" * 60)
        logger.info("Training Collaborative Filtering Model")
        logger.info("=" * 60)
        
        # Load interaction features
        storage = DataLakeStorage()
        interactions_df = storage.load_training('interaction_features', 'features')
        
        # Initialize and train model
        cf_model = CollaborativeFilteringModel()
        dataset = cf_model.prepare_data(interactions_df)
        trainset, testset = cf_model.train(dataset)
        
        # Save model
        model_dir = Path('models')
        model_dir.mkdir(exist_ok=True)
        cf_model.save_model(str(model_dir / 'collaborative_filtering.pkl'))
        
        # Test recommendation
        sample_user = interactions_df['user_id'].iloc[0]
        all_items = interactions_df['item_id'].unique().tolist()
        user_items = interactions_df[interactions_df['user_id'] == sample_user]['item_id'].tolist()
        
        recommendations = cf_model.generate_recommendations(sample_user, all_items, user_items, top_k=10)
        
        logger.info(f"\nSample recommendations for user {sample_user}:")
        for rec in recommendations[:5]:
            logger.info(f"  Item {rec['item_id']}: score={rec['predicted_score']:.3f}")
        
        logger.info("=" * 60)
        logger.info(" Collaborative filtering training complete")
        logger.info("=" * 60)
        
        return 0
    
    except Exception as e:
        logger.critical(f"CF training failed: {str(e)}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
