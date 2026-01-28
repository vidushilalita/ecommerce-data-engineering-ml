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
import mlflow
import mlflow.sklearn
from datetime import datetime

from surprise import SVD, Dataset, Reader
from surprise.model_selection import train_test_split, cross_validate

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.logger import get_logger
from src.utils.storage import DataLakeStorage

logger = get_logger(__name__)


class CollaborativeFilteringModel:
    """Collaborative filtering recommendation model using SVD"""
    
    def __init__(self, n_factors: int = 50, n_epochs: int = 20, lr_all: float = 0.005, reg_all: float = 0.02, 
                 experiment_name: str = "CF-SVD-Recommendations"):
        """
        Initialize CF model
        
        Args:
            n_factors: Number of latent factors
            n_epochs: Number of training epochs
            lr_all: Learning rate
            reg_all: Regularization parameter
            experiment_name: MLflow experiment name
        """
        self.n_factors = n_factors
        self.n_epochs = n_epochs
        self.lr_all = lr_all
        self.reg_all = reg_all
        self.experiment_name = experiment_name
        
        self.model = SVD(
            n_factors=n_factors,
            n_epochs=n_epochs,
            lr_all=lr_all,
            reg_all=reg_all,
            random_state=42
        )
        self.storage = DataLakeStorage()
        self.trained = False
        
        # Setup MLflow
        mlflow.set_experiment(experiment_name)
        
        logger.info(f"Initialized SVD model with {n_factors} factors, {n_epochs} epochs")
        logger.info(f"MLflow experiment: {experiment_name}")
    
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
        """Train the model with integrated evaluation, logging to same MLflow run"""
        logger.info("Training collaborative filtering model...")
        
        with mlflow.start_run(run_name=f"CF-SVD-{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
            # Log parameters
            mlflow.log_params({
                'n_factors': self.n_factors,
                'n_epochs': self.n_epochs,
                'lr_all': self.lr_all,
                'reg_all': self.reg_all,
                'test_size': test_size,
                'random_state': 42
            })
            
            # Split train/test
            trainset, testset = train_test_split(dataset, test_size=test_size, random_state=42)
            
            logger.info(f"Training set: {trainset.n_ratings} ratings")
            logger.info(f"Test set: {len(testset)} ratings")
            
            # Log dataset info
            mlflow.log_metrics({
                'train_ratings': trainset.n_ratings,
                'test_ratings': len(testset),
                'dataset_size': trainset.n_ratings + len(testset)
            })
            
            # Train
            self.model.fit(trainset)
            self.trained = True
            
            # Cross-validation metrics
            cv_results = cross_validate(self.model, dataset, measures=['rmse', 'mae'], cv=5, verbose=False)
            avg_rmse = np.mean(cv_results['test_rmse'])
            avg_mae = np.mean(cv_results['test_mae'])
            
            mlflow.log_metrics({
                'cv_rmse': avg_rmse,
                'cv_mae': avg_mae,
                'cv_rmse_std': np.std(cv_results['test_rmse']),
                'cv_mae_std': np.std(cv_results['test_mae'])
            })
            
            logger.info(f"CV RMSE: {avg_rmse:.4f} ± {np.std(cv_results['test_rmse']):.4f}")
            logger.info(f"CV MAE: {avg_mae:.4f} ± {np.std(cv_results['test_mae']):.4f}")
            
            # ==================== AUTO EVALUATION ====================
            logger.info("\nRunning model evaluation on test set...")
            eval_metrics = self._evaluate_on_testset(testset)
            
            # Log evaluation metrics to the same MLflow run
            mlflow.log_metrics(eval_metrics)
            
            logger.info("Model training and evaluation complete")
        
        return trainset, testset
    
    def _evaluate_on_testset(self, testset: list) -> Dict[str, float]:
        """
        Evaluate model on test set and return metrics.
        Uses sklearn for prediction accuracy metrics.
        """
        from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
        
        logger.info("\nEvaluation Metrics:")
        
        # Generate predictions
        true_ratings = []
        predicted_ratings = []
        
        for uid, iid, true_rating in testset:
            pred = self.model.predict(uid, iid)
            true_ratings.append(true_rating)
            predicted_ratings.append(pred.est)
        
        true_ratings = np.array(true_ratings)
        predicted_ratings = np.array(predicted_ratings)
        
        # Calculate metrics using sklearn
        rmse = np.sqrt(mean_squared_error(true_ratings, predicted_ratings))
        mae = mean_absolute_error(true_ratings, predicted_ratings)
        r2 = r2_score(true_ratings, predicted_ratings)
        mape = np.mean(np.abs((true_ratings - predicted_ratings) / true_ratings)) * 100
        
        metrics = {
            'test_rmse': rmse,
            'test_mae': mae,
            'test_r2': r2,
            'test_mape': mape,
            'test_mean_prediction': float(np.mean(predicted_ratings)),
            'test_mean_actual': float(np.mean(true_ratings))
        }
        
        logger.info(f"  Test RMSE: {rmse:.4f}")
        logger.info(f"  Test MAE:  {mae:.4f}")
        logger.info(f"  Test R²:   {r2:.4f}")
        logger.info(f"  Test MAPE: {mape:.2f}%")
        
        # ==================== RANKING METRICS ====================
        # Evaluate ranking metrics
        ranking_metrics = self._calculate_ranking_metrics(testset)
        metrics.update(ranking_metrics)
        
        for metric_name, value in ranking_metrics.items():
            logger.info(f"  {metric_name}: {value:.4f}")
        
        return metrics
    
    def _calculate_ranking_metrics(self, testset: list, k_values: List[int] = [5, 10, 20]) -> Dict[str, float]:
        """Calculate ranking metrics (Precision@K, Recall@K, NDCG@K, Hit Rate@K, MRR)"""
        
        # Build user predictions and ground truth
        user_predictions = {}
        user_true_positives = {}
        
        for uid, iid, true_rating in testset:
            if uid not in user_predictions:
                user_predictions[uid] = []
                user_true_positives[uid] = set()
            
            pred = self.model.predict(uid, iid)
            user_predictions[uid].append((iid, pred.est))
            
            # Items with rating > 2.5 are considered relevant
            if true_rating > 2.5:
                user_true_positives[uid].add(iid)
        
        # Sort predictions by score for each user
        for uid in user_predictions:
            user_predictions[uid].sort(key=lambda x: x[1], reverse=True)
            user_predictions[uid] = [iid for iid, _ in user_predictions[uid]]
        
        ranking_metrics = {}
        
        # Calculate metrics for each K
        for k in k_values:
            precision_scores = []
            recall_scores = []
            ndcg_scores = []
            hit_rate_scores = []
            
            for uid in user_predictions:
                if uid not in user_true_positives or len(user_true_positives[uid]) == 0:
                    continue
                
                recommended = user_predictions[uid]
                relevant = user_true_positives[uid]
                
                precision_scores.append(self._precision_at_k(recommended, relevant, k))
                recall_scores.append(self._recall_at_k(recommended, relevant, k))
                ndcg_scores.append(self._ndcg_at_k(recommended, relevant, k))
                hit_rate_scores.append(self._hit_rate_at_k(recommended, relevant, k))
            
            if precision_scores:
                ranking_metrics[f'precision@{k}'] = np.mean(precision_scores)
                ranking_metrics[f'recall@{k}'] = np.mean(recall_scores)
                ranking_metrics[f'ndcg@{k}'] = np.mean(ndcg_scores)
                ranking_metrics[f'hit_rate@{k}'] = np.mean(hit_rate_scores)
        
        # MRR (not k-dependent)
        mrr_scores = []
        for uid in user_predictions:
            if uid in user_true_positives and len(user_true_positives[uid]) > 0:
                recommended = user_predictions[uid]
                relevant = user_true_positives[uid]
                mrr_scores.append(self._mrr(recommended, relevant))
        
        if mrr_scores:
            ranking_metrics['mrr'] = np.mean(mrr_scores)
        
        return ranking_metrics
    
    # ==================== RANKING METRIC HELPERS ====================
    
    @staticmethod
    def _precision_at_k(recommended: List[int], relevant: set, k: int) -> float:
        """Precision@K"""
        if len(recommended) == 0:
            return 0.0
        return len(set(recommended[:k]) & relevant) / min(len(recommended[:k]), k)
    
    @staticmethod
    def _recall_at_k(recommended: List[int], relevant: set, k: int) -> float:
        """Recall@K"""
        if len(relevant) == 0:
            return 0.0
        return len(set(recommended[:k]) & relevant) / len(relevant)
    
    @staticmethod
    def _ndcg_at_k(recommended: List[int], relevant: set, k: int) -> float:
        """NDCG@K"""
        recommended_k = recommended[:k]
        dcg = sum(1.0 / np.log2(i + 2) for i, iid in enumerate(recommended_k) if iid in relevant)
        idcg = sum(1.0 / np.log2(i + 2) for i in range(min(len(relevant), k)))
        return dcg / idcg if idcg > 0 else 0.0
    
    @staticmethod
    def _hit_rate_at_k(recommended: List[int], relevant: set, k: int) -> float:
        """Hit Rate@K"""
        return 1.0 if len(set(recommended[:k]) & relevant) > 0 else 0.0
    
    @staticmethod
    def _mrr(recommended: List[int], relevant: set) -> float:
        """MRR - Mean Reciprocal Rank"""
        for i, item_id in enumerate(recommended):
            if item_id in relevant:
                return 1.0 / (i + 1)
        return 0.0
    
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
        """Save trained model and log to MLflow"""
        with open(filepath, 'wb') as f:
            pickle.dump(self.model, f)
        
        # Log model artifact to MLflow
        mlflow.log_artifact(filepath, artifact_path='models')
        logger.info(f"Saved model to {filepath}")
        logger.info(f"Logged model artifact to MLflow")
    
    def load_model(self, filepath: str):
        """Load trained model"""
        with open(filepath, 'rb') as f:
            self.model = pickle.load(f)
        self.trained = True
        logger.info(f"Loaded model from {filepath}")


def main():
    """Main execution with MLflow tracking"""
    try:
        logger.info("=" * 60)
        logger.info("Training Collaborative Filtering Model")
        logger.info("=" * 60)
        
        # Load interaction features
        storage = DataLakeStorage()
        interactions_df = storage.load_latest('interaction_features', 'features')
        
        # Initialize and train model with MLflow
        cf_model = CollaborativeFilteringModel(
            n_factors=50,
            n_epochs=20,
            lr_all=0.005,
            reg_all=0.02,
            experiment_name="CF-SVD-Recommendations"
        )
        
        dataset = cf_model.prepare_data(interactions_df)
        trainset, testset = cf_model.train(dataset)
        
        # Save model
        model_dir = Path('models')
        model_dir.mkdir(exist_ok=True)
        model_path = str(model_dir / 'collaborative_filtering.pkl')
        cf_model.save_model(model_path)
        
        # Test recommendation
        sample_user = interactions_df['user_id'].iloc[0]
        all_items = interactions_df['item_id'].unique().tolist()
        user_items = interactions_df[interactions_df['user_id'] == sample_user]['item_id'].tolist()
        
        recommendations = cf_model.generate_recommendations(sample_user, all_items, user_items, top_k=10)
        
        logger.info(f"\nSample recommendations for user {sample_user}:")
        for rec in recommendations[:5]:
            logger.info(f"  Item {rec['item_id']}: score={rec['predicted_score']:.3f}")
        
        # Log sample recommendations to MLflow
        mlflow.log_metric('sample_user_id', sample_user)
        mlflow.log_metric('total_items', len(all_items))
        mlflow.log_metric('user_interactions', len(user_items))
        
        logger.info("=" * 60)
        logger.info("Collaborative filtering training complete")
        logger.info("=" * 60)
        
        return 0
    
    except Exception as e:
        logger.critical(f"CF training failed: {str(e)}", exc_info=True)
        mlflow.end_run()
        return 1


if __name__ == '__main__':
    sys.exit(main())
