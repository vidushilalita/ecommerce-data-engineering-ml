"""
Model Evaluation Module

Evaluates trained SVD models using scikit-learn metrics + ranking metrics.
Calculates both prediction accuracy (RMSE, MAE, R²) and ranking metrics:
- Precision@K, Recall@K, NDCG@K, Hit Rate@K, MRR
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Set, Any
import mlflow
from datetime import datetime
import json

from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.logger import get_logger
from src.utils.storage import DataLakeStorage

logger = get_logger(__name__)


class ModelEvaluator:
    """
    Evaluates trained SVD models on test data using sklearn metrics + ranking metrics.
    
    Prediction Metrics:
    - RMSE (Root Mean Squared Error)
    - MAE (Mean Absolute Error)  
    - R² Score (Coefficient of Determination)
    - MAPE (Mean Absolute Percentage Error)
    
    Ranking Metrics:
    - Precision@K, Recall@K, NDCG@K, Hit Rate@K, MRR
    """
    
    def __init__(self, experiment_name: str = "Model-Evaluation"):
        """Initialize evaluator with MLflow tracking"""
        self.experiment_name = experiment_name
        mlflow.set_experiment(experiment_name)
        self.storage = DataLakeStorage()
        logger.info("Initialized ModelEvaluator")
        logger.info(f"MLflow experiment: {experiment_name}")
    
    # ==================== RANKING METRICS ====================
    
    @staticmethod
    def precision_at_k(recommended: List[int], relevant: Set[int], k: int) -> float:
        """Calculate Precision@K - fraction of recommended items that are relevant"""
        recommended_k = recommended[:k]
        if len(recommended_k) == 0:
            return 0.0
        relevant_recommended = len(set(recommended_k) & relevant)
        return relevant_recommended / len(recommended_k)
    
    @staticmethod
    def recall_at_k(recommended: List[int], relevant: Set[int], k: int) -> float:
        """Calculate Recall@K - fraction of relevant items that are recommended"""
        if len(relevant) == 0:
            return 0.0
        recommended_k = recommended[:k]
        relevant_recommended = len(set(recommended_k) & relevant)
        return relevant_recommended / len(relevant)
    
    @staticmethod
    def ndcg_at_k(recommended: List[int], relevant: Set[int], k: int) -> float:
        """Calculate NDCG@K - Normalized Discounted Cumulative Gain"""
        recommended_k = recommended[:k]
        
        # DCG (Discounted Cumulative Gain)
        dcg = 0.0
        for i, item_id in enumerate(recommended_k):
            if item_id in relevant:
                dcg += 1.0 / np.log2(i + 2)  # i+2 because index starts at 0
        
        # IDCG (Ideal DCG - all relevant items at top)
        idcg = 0.0
        for i in range(min(len(relevant), k)):
            idcg += 1.0 / np.log2(i + 2)
        
        if idcg == 0:
            return 0.0
        
        return dcg / idcg
    
    @staticmethod
    def hit_rate_at_k(recommended: List[int], relevant: Set[int], k: int) -> float:
        """Calculate Hit Rate@K - whether there's at least one relevant item in top-K"""
        recommended_k = recommended[:k]
        relevant_recommended = set(recommended_k) & relevant
        return 1.0 if len(relevant_recommended) > 0 else 0.0
    
    @staticmethod
    def mrr(recommended: List[int], relevant: Set[int]) -> float:
        """Calculate MRR - Mean Reciprocal Rank (position of first relevant item)"""
        for i, item_id in enumerate(recommended):
            if item_id in relevant:
                return 1.0 / (i + 1)
        return 0.0
    
    def evaluate_model_on_testset(
        self,
        model: Any,
        testset: list,
        log_to_mlflow: bool = True
    ) -> Dict[str, float]:
        """
        Evaluate trained SVD model on test set using sklearn metrics
        
        Args:
            model: Trained SVD model from Surprise library
            testset: Test set from train_test_split (list of tuples: uid, iid, rating)
            log_to_mlflow: Whether to log metrics to MLflow
        
        Returns:
            Dictionary with RMSE, MAE, R², MAPE
        """
        logger.info("Evaluating model on test set...")
        
        if log_to_mlflow:
            mlflow.start_run(run_name=f"Evaluation-{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            mlflow.log_params({'test_set_size': len(testset), 'model_type': 'SVD'})
        
        # Generate predictions on test set
        true_ratings = []
        predicted_ratings = []
        
        for uid, iid, true_rating in testset:
            pred = model.predict(uid, iid)
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
            'rmse': rmse,
            'mae': mae,
            'r2': r2,
            'mape': mape,
            'num_predictions': len(testset),
            'mean_true_rating': float(np.mean(true_ratings)),
            'std_true_rating': float(np.std(true_ratings))
        }
        
        logger.info(f"Test Set Metrics:")
        logger.info(f"  RMSE: {rmse:.4f}")
        logger.info(f"  MAE:  {mae:.4f}")
        logger.info(f"  R²:   {r2:.4f}")
        logger.info(f"  MAPE: {mape:.2f}%")
        
        if log_to_mlflow:
            mlflow.log_metrics(metrics)
            mlflow.end_run()
        
        return metrics
    
    def evaluate_ranking_on_testset(
        self,
        model: Any,
        testset: list,
        k_values: List[int] = [5, 10, 20],
        log_to_mlflow: bool = True
    ) -> Dict[str, Dict[str, float]]:
        """
        Evaluate ranking metrics on test set (Precision@K, Recall@K, NDCG@K, Hit Rate, MRR)
        
        Args:
            model: Trained SVD model from Surprise library
            testset: Test set from train_test_split
            k_values: List of K values to evaluate
            log_to_mlflow: Whether to log metrics to MLflow
        
        Returns:
            Dictionary of ranking metrics (mean, std, min, max for each metric)
        """
        logger.info("Evaluating ranking metrics on test set...")
        
        if log_to_mlflow:
            mlflow.start_run(run_name=f"Ranking-Eval-{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            mlflow.log_params({'k_values': str(k_values), 'test_set_size': len(testset)})
        
        # Generate predictions for all items for each user
        user_predictions = {}
        user_true_positives = {}
        
        for uid, iid, true_rating in testset:
            if uid not in user_predictions:
                user_predictions[uid] = []
                user_true_positives[uid] = set()
            
            pred = model.predict(uid, iid)
            user_predictions[uid].append((iid, pred.est))
            
            # Items with rating > 2.5 are considered relevant
            if true_rating > 2.5:
                user_true_positives[uid].add(iid)
        
        # Sort predictions by score for each user
        for uid in user_predictions:
            user_predictions[uid].sort(key=lambda x: x[1], reverse=True)
            user_predictions[uid] = [iid for iid, _ in user_predictions[uid]]
        
        # Calculate ranking metrics
        ranking_results = {}
        
        for k in k_values:
            precision_scores = []
            recall_scores = []
            ndcg_scores = []
            hit_rate_scores = []
            mrr_scores = []
            
            for uid in user_predictions:
                if uid not in user_true_positives or len(user_true_positives[uid]) == 0:
                    continue
                
                recommended = user_predictions[uid]
                relevant = user_true_positives[uid]
                
                precision_scores.append(self.precision_at_k(recommended, relevant, k))
                recall_scores.append(self.recall_at_k(recommended, relevant, k))
                ndcg_scores.append(self.ndcg_at_k(recommended, relevant, k))
                hit_rate_scores.append(self.hit_rate_at_k(recommended, relevant, k))
            
            # MRR is not k-dependent
            if k == k_values[0]:  # Calculate once
                for uid in user_predictions:
                    if uid in user_true_positives and len(user_true_positives[uid]) > 0:
                        recommended = user_predictions[uid]
                        relevant = user_true_positives[uid]
                        mrr_scores.append(self.mrr(recommended, relevant))
            
            ranking_results[f'precision@{k}'] = {
                'mean': np.mean(precision_scores) if precision_scores else 0.0,
                'std': np.std(precision_scores) if precision_scores else 0.0,
                'min': np.min(precision_scores) if precision_scores else 0.0,
                'max': np.max(precision_scores) if precision_scores else 0.0
            }
            
            ranking_results[f'recall@{k}'] = {
                'mean': np.mean(recall_scores) if recall_scores else 0.0,
                'std': np.std(recall_scores) if recall_scores else 0.0,
                'min': np.min(recall_scores) if recall_scores else 0.0,
                'max': np.max(recall_scores) if recall_scores else 0.0
            }
            
            ranking_results[f'ndcg@{k}'] = {
                'mean': np.mean(ndcg_scores) if ndcg_scores else 0.0,
                'std': np.std(ndcg_scores) if ndcg_scores else 0.0,
                'min': np.min(ndcg_scores) if ndcg_scores else 0.0,
                'max': np.max(ndcg_scores) if ndcg_scores else 0.0
            }
            
            ranking_results[f'hit_rate@{k}'] = {
                'mean': np.mean(hit_rate_scores) if hit_rate_scores else 0.0,
                'std': np.std(hit_rate_scores) if hit_rate_scores else 0.0,
                'min': np.min(hit_rate_scores) if hit_rate_scores else 0.0,
                'max': np.max(hit_rate_scores) if hit_rate_scores else 0.0
            }
        
        # MRR (not k-dependent)
        ranking_results['mrr'] = {
            'mean': np.mean(mrr_scores) if mrr_scores else 0.0,
            'std': np.std(mrr_scores) if mrr_scores else 0.0,
            'min': np.min(mrr_scores) if mrr_scores else 0.0,
            'max': np.max(mrr_scores) if mrr_scores else 0.0
        }
        
        # Log metrics to MLflow
        if log_to_mlflow:
            for metric_name, stats in ranking_results.items():
                mlflow.log_metrics({
                    f'{metric_name}_mean': stats['mean'],
                    f'{metric_name}_std': stats['std'],
                    f'{metric_name}_min': stats['min'],
                    f'{metric_name}_max': stats['max']
                })
            
            mlflow.log_metric('num_users_evaluated', len(user_predictions))
            mlflow.end_run()
        
        logger.info("Ranking evaluation complete")
        
        return ranking_results
    
    def print_evaluation_results(self, metrics: Dict[str, float], save_to_file: bool = True):
        """Print and save prediction metrics results"""
        logger.info("\n" + "=" * 60)
        logger.info("PREDICTION METRICS (Test Set Performance)")
        logger.info("=" * 60)
        
        logger.info(f"\nAccuracy Metrics:")
        logger.info(f"  RMSE (Root Mean Squared Error): {metrics['rmse']:.4f}")
        logger.info(f"  MAE (Mean Absolute Error):     {metrics['mae']:.4f}")
        logger.info(f"  R² Score:                       {metrics['r2']:.4f}")
        logger.info(f"  MAPE (Mean Absolute % Error):  {metrics['mape']:.2f}%")
        logger.info(f"\nDataset Info:")
        logger.info(f"  Test Predictions:               {metrics['num_predictions']}")
        logger.info(f"  Mean True Rating:               {metrics['mean_true_rating']:.2f}")
        logger.info(f"  Std True Rating:                {metrics['std_true_rating']:.2f}")
        
        logger.info("=" * 60 + "\n")
        
        # Save results to file
        if save_to_file:
            results_path = Path('reports') / f"model_evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            results_path.parent.mkdir(parents=True, exist_ok=True)
            
            json_metrics = {k: float(v) for k, v in metrics.items()}
            
            with open(results_path, 'w') as f:
                json.dump(json_metrics, f, indent=2)
            
            logger.info(f"Evaluation results saved to {results_path}")
    
    def print_ranking_results(self, results: Dict[str, Dict[str, float]], save_to_file: bool = True):
        """Print and save ranking metrics results"""
        logger.info("\n" + "=" * 60)
        logger.info("RANKING METRICS (Test Set Performance)")
        logger.info("=" * 60)
        
        for metric_name, stats in results.items():
            logger.info(f"\n{metric_name.upper()}:")
            logger.info(f"  Mean: {stats['mean']:.4f}")
            logger.info(f"  Std:  {stats['std']:.4f}")
            logger.info(f"  Min:  {stats['min']:.4f}")
            logger.info(f"  Max:  {stats['max']:.4f}")
        
        logger.info("=" * 60 + "\n")
        
        # Save results to file
        if save_to_file:
            results_path = Path('reports') / f"ranking_evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            results_path.parent.mkdir(parents=True, exist_ok=True)
            
            json_results = {k: {kk: float(vv) for kk, vv in v.items()} for k, v in results.items()}
            
            with open(results_path, 'w') as f:
                json.dump(json_results, f, indent=2)
            
            logger.info(f"Ranking evaluation results saved to {results_path}")


def main():
    """Test evaluation with actual model and test data"""
    try:
        logger.info("=" * 60)
        logger.info("Comprehensive Model Evaluation")
        logger.info("=" * 60)
        
        from src.model_training.collaborative_filtering import CollaborativeFilteringModel
        
        # Load data
        storage = DataLakeStorage()
        interactions_df = storage.load_latest('interaction_features', 'features')
        
        logger.info(f"Loaded {len(interactions_df)} interaction records")
        
        # Train model
        cf_model = CollaborativeFilteringModel()
        dataset = cf_model.prepare_data(interactions_df)
        trainset, testset = cf_model.train(dataset)
        
        logger.info(f"Train set: {trainset.n_ratings} ratings")
        logger.info(f"Test set: {len(testset)} ratings")
        
        # Evaluate prediction metrics
        evaluator = ModelEvaluator(experiment_name="Model-Evaluation")
        
        prediction_metrics = evaluator.evaluate_model_on_testset(
            cf_model.model,
            testset,
            log_to_mlflow=True
        )
        evaluator.print_evaluation_results(prediction_metrics, save_to_file=True)
        
        # Evaluate ranking metrics
        ranking_metrics = evaluator.evaluate_ranking_on_testset(
            cf_model.model,
            testset,
            k_values=[5, 10, 20],
            log_to_mlflow=True
        )
        evaluator.print_ranking_results(ranking_metrics, save_to_file=True)
        
        logger.info("Evaluation completed successfully")
        return 0
    
    except Exception as e:
        logger.critical(f"Evaluation failed: {str(e)}", exc_info=True)
        mlflow.end_run()
        return 1


if __name__ == '__main__':
    sys.exit(main())
