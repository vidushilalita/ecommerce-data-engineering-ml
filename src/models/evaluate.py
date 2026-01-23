"""
Model Evaluation Module

Evaluates recommendation models using metrics:
- Precision@K
- Recall@K
- NDCG@K
- Hit Rate
- MRR (Mean Reciprocal Rank)
"""

import sys
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.logger import get_logger

logger = get_logger(__name__)


class RecommendationEvaluator:
    """Evaluation metrics for recommendation systems"""
    
    def __init__(self):
        """Initialize evaluator"""
        logger.info("Initialized RecommendationEvaluator")
    
    @staticmethod
    def precision_at_k(recommended: List[int], relevant: Set[int], k: int) -> float:
        """Calculate Precision@K"""
        recommended_k = recommended[:k]
        relevant_recommended = set(recommended_k) & relevant
        
        if len(recommended_k) == 0:
            return 0.0
        
        return len(relevant_recommended) / len(recommended_k)
    
    @staticmethod
    def recall_at_k(recommended: List[int], relevant: Set[int], k: int) -> float:
        """Calculate Recall@K"""
        if len(relevant) == 0:
            return 0.0
        
        recommended_k = recommended[:k]
        relevant_recommended = set(recommended_k) & relevant
        
        return len(relevant_recommended) / len(relevant)
    
    @staticmethod
    def ndcg_at_k(recommended: List[int], relevant: Set[int], k: int) -> float:
        """Calculate NDCG@K (Normalized Discounted Cumulative Gain)"""
        recommended_k = recommended[:k]
        
        # DCG
        dcg = 0.0
        for i, item_id in enumerate(recommended_k):
            if item_id in relevant:
                # Relevance = 1 if relevant, 0 otherwise
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
        """Calculate whether there's at least one hit in top-K"""
        recommended_k = recommended[:k]
        relevant_recommended = set(recommended_k) & relevant
        
        return 1.0 if len(relevant_recommended) > 0 else 0.0
    
    @staticmethod
    def mrr(recommended: List[int], relevant: Set[int]) -> float:
        """Calculate Mean Reciprocal Rank"""
        for i, item_id in enumerate(recommended):
            if item_id in relevant:
                return 1.0 / (i + 1)
        return 0.0
    
    def evaluate_recommendations(
        self,
        all_recommendations: Dict[int, List[int]],
        ground_truth: Dict[int, Set[int]],
        k_values: List[int] = [5, 10, 20]
    ) -> Dict[str, Dict[int, float]]:
        """
        Evaluate recommendations for all users
        
        Args:
            all_recommendations: Dict mapping user_id to list of recommended item_ids
            ground_truth: Dict mapping user_id to set of relevant item_ids
            k_values: List of K values to evaluate
        
        Returns:
            Dictionary of metrics
        """
        logger.info("Evaluating recommendations...")
        
        results = defaultdict(lambda: defaultdict(list))
        
        for user_id in all_recommendations.keys():
            if user_id not in ground_truth:
                continue
            
            recommended = all_recommendations[user_id]
            relevant = ground_truth[user_id]
            
            if len(relevant) == 0:
                continue
            
            # Calculate metrics for each K
            for k in k_values:
                results[f'precision@{k}'][user_id] = self.precision_at_k(recommended, relevant, k)
                results[f'recall@{k}'][user_id] = self.recall_at_k(recommended, relevant, k)
                results[f'ndcg@{k}'][user_id] = self.ndcg_at_k(recommended, relevant, k)
                results[f'hit_rate@{k}'][user_id] = self.hit_rate_at_k(recommended, relevant, k)
            
            # MRR (not K-dependent)
            results['mrr'][user_id] = self.mrr(recommended, relevant)
        
        # Average metrics across users
        averaged_results = {}
        for metric_name, user_scores in results.items():
            scores = list(user_scores.values())
            averaged_results[metric_name] = {
                'mean': np.mean(scores),
                'std': np.std(scores),
                'min': np.min(scores),
                'max': np.max(scores)
            }
        
        logger.info("✓ Evaluation complete")
        
        return averaged_results
    
    def print_evaluation_results(self, results: Dict[str, Dict[str, float]]):
        """Print formatted evaluation results"""
        logger.info("\n" + "=" * 60)
        logger.info("EVALUATION RESULTS")
        logger.info("=" * 60)
        
        for metric_name, stats in results.items():
            logger.info(f"\n{metric_name.upper()}:")
            logger.info(f"  Mean: {stats['mean']:.4f}")
            logger.info(f"  Std:  {stats['std']:.4f}")
            logger.info(f"  Min:  {stats['min']:.4f}")
            logger.info(f"  Max:  {stats['max']:.4f}")
        
        logger.info("=" * 60)


def main():
    """Test evaluation"""
    # Example usage
    evaluator = RecommendationEvaluator()
    
    # Simulate recommendations and ground truth
    all_recs = {
        1: [101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
        2: [201, 202, 203, 204, 205, 206, 207, 208, 209, 210],
    }
    
    ground_truth = {
        1: {102, 105, 120, 130},
        2: {201, 210, 220, 230},
    }
    
    results = evaluator.evaluate_recommendations(all_recs, ground_truth, k_values=[5, 10])
    evaluator.print_evaluation_results(results)


if __name__ == '__main__':
    main()
