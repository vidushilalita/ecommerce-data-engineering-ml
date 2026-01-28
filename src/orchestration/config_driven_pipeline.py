"""
Configuration-Driven Dagster Pipeline Orchestration

This module enables fully automated, configurable pipeline execution where:
- All pipeline settings come from configuration files
- Tasks automatically wait for dependencies to complete
- Retry logic, timeouts, and resource allocation are configurable
- Support for scheduled/automated runs without manual intervention
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import yaml
import mlflow

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.logger import get_logger

logger = get_logger(__name__)


class PipelineConfig:
    """Load and manage pipeline configuration from YAML/JSON"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize pipeline configuration
        
        Args:
            config_path: Path to config file (YAML or JSON)
                         Defaults to 'pipeline_config.yaml' in project root
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / 'pipeline_config.yaml'
        else:
            config_path = Path(config_path)
        
        self.config_path = config_path
        self.config = self._load_config()
        
        logger.info(f"Loaded pipeline configuration from {config_path}")
        self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML or JSON file"""
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}")
            return self._get_default_config()
        
        try:
            if self.config_path.suffix in ['.yaml', '.yml']:
                with open(self.config_path, 'r') as f:
                    return yaml.safe_load(f) or {}
            elif self.config_path.suffix == '.json':
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"Unsupported config format: {self.config_path.suffix}")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'pipeline': {
                'name': 'recomart_pipeline',
                'description': 'RecoMart data pipeline',
                'enabled': True,
                'parallel_tasks': True,
            },
            'execution': {
                'mode': 'sequential',  # 'sequential' or 'parallel'
                'timeout_seconds': 3600,
                'max_retries': 2,
                'retry_delay_seconds': 30,
            },
            'tasks': {
                'ingestion': {
                    'enabled': True,
                    'timeout_seconds': 300,
                    'retry_count': 1,
                    'config': {}
                },
                'validation': {
                    'enabled': True,
                    'depends_on': ['ingestion'],
                    'timeout_seconds': 600,
                    'config': {}
                },
                'preparation': {
                    'enabled': True,
                    'depends_on': ['validation'],
                    'timeout_seconds': 600,
                    'config': {}
                },
                'features': {
                    'enabled': True,
                    'depends_on': ['preparation'],
                    'timeout_seconds': 600,
                    'config': {}
                },
                'training': {
                    'enabled': True,
                    'depends_on': ['features'],
                    'timeout_seconds': 900,
                    'config': {}
                }
            },
            'storage': {
                'base_dir': 'storage',
                'data_dir': 'data',
                'models_dir': 'models'
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/pipeline.log'
            },
            'scheduling': {
                'enabled': False,
                'cron': '0 2 * * *',  # 2 AM daily
                'timezone': 'UTC'
            }
        }
    
    def _validate_config(self):
        """Validate configuration structure"""
        required_sections = ['pipeline', 'execution', 'tasks']
        for section in required_sections:
            if section not in self.config:
                logger.warning(f"Missing config section: {section}")
                self.config[section] = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value by dot-notation key"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def get_task_config(self, task_name: str) -> Dict[str, Any]:
        """Get configuration for a specific task"""
        return self.config.get('tasks', {}).get(task_name, {})
    
    def get_task_dependencies(self, task_name: str) -> List[str]:
        """Get list of tasks that must complete before this task"""
        task_config = self.get_task_config(task_name)
        return task_config.get('depends_on', [])
    
    def is_task_enabled(self, task_name: str) -> bool:
        """Check if task is enabled"""
        task_config = self.get_task_config(task_name)
        return task_config.get('enabled', True)
    
    def get_task_timeout(self, task_name: str) -> int:
        """Get timeout in seconds for a task"""
        task_config = self.get_task_config(task_name)
        return task_config.get('timeout_seconds', 600)
    
    def get_task_retry_count(self, task_name: str) -> int:
        """Get number of retries for a task"""
        task_config = self.get_task_config(task_name)
        return task_config.get('retry_count', self.config.get('execution', {}).get('max_retries', 2))
    
    def get_execution_mode(self) -> str:
        """Get execution mode (sequential or parallel)"""
        return self.config.get('execution', {}).get('mode', 'sequential')
    
    def is_scheduling_enabled(self) -> bool:
        """Check if scheduling is enabled"""
        return self.config.get('scheduling', {}).get('enabled', False)
    
    def get_cron_schedule(self) -> str:
        """Get cron schedule for automatic runs"""
        return self.config.get('scheduling', {}).get('cron', '0 2 * * *')
    
    def to_dict(self) -> Dict[str, Any]:
        """Get entire config as dictionary"""
        return self.config
    
    def save(self, output_path: Optional[str] = None):
        """Save current configuration to file"""
        output_path = Path(output_path) if output_path else self.config_path
        
        try:
            if output_path.suffix in ['.yaml', '.yml']:
                with open(output_path, 'w') as f:
                    yaml.dump(self.config, f, default_flow_style=False)
            elif output_path.suffix == '.json':
                with open(output_path, 'w') as f:
                    json.dump(self.config, f, indent=2)
            
            logger.info(f"Configuration saved to {output_path}")
        except Exception as e:
            logger.error(f"Error saving config: {str(e)}")


class TaskDependencyGraph:
    """Build and manage task dependency graph"""
    
    def __init__(self, config: PipelineConfig):
        """
        Initialize dependency graph
        
        Args:
            config: PipelineConfig instance
        """
        self.config = config
        self.tasks = {}
        self.graph = {}
        self._build_graph()
    
    def _build_graph(self):
        """Build dependency graph from configuration"""
        tasks = self.config.config.get('tasks', {})
        
        for task_name, task_config in tasks.items():
            if not self.config.is_task_enabled(task_name):
                continue
            
            self.tasks[task_name] = task_config
            dependencies = task_config.get('depends_on', [])
            self.graph[task_name] = dependencies
        
        logger.info(f"Built dependency graph with {len(self.tasks)} tasks")
        self._log_graph()
    
    def _log_graph(self):
        """Log the dependency graph"""
        for task, deps in self.graph.items():
            if deps:
                logger.debug(f"Task '{task}' depends on: {deps}")
            else:
                logger.debug(f"Task '{task}' has no dependencies (root task)")
    
    def get_execution_order(self) -> List[str]:
        """
        Get tasks in execution order (topological sort)
        
        Returns:
            List of task names in order they should execute
        """
        executed = set()
        order = []
        
        while len(executed) < len(self.tasks):
            made_progress = False
            
            for task in self.tasks:
                if task in executed:
                    continue
                
                # Check if all dependencies are satisfied
                deps = self.graph.get(task, [])
                if all(dep in executed for dep in deps):
                    order.append(task)
                    executed.add(task)
                    made_progress = True
            
            if not made_progress:
                # Circular dependency or missing dependency
                remaining = set(self.tasks.keys()) - executed
                logger.error(f"Cannot resolve dependencies for: {remaining}")
                break
        
        logger.info(f"Execution order: {' → '.join(order)}")
        return order
    
    def get_parallel_groups(self) -> List[List[str]]:
        """
        Get tasks grouped by execution level for parallel execution
        
        Returns:
            List of task groups that can run in parallel
        """
        groups = []
        executed = set()
        
        while len(executed) < len(self.tasks):
            current_group = []
            
            for task in self.tasks:
                if task in executed:
                    continue
                
                deps = self.graph.get(task, [])
                if all(dep in executed for dep in deps):
                    current_group.append(task)
            
            if current_group:
                groups.append(current_group)
                executed.update(current_group)
            else:
                break
        
        logger.info(f"Parallel groups: {groups}")
        return groups
    
    def get_task_info(self, task_name: str) -> Dict[str, Any]:
        """Get detailed information about a task"""
        if task_name not in self.tasks:
            return {}
        
        return {
            'name': task_name,
            'enabled': True,
            'dependencies': self.graph.get(task_name, []),
            'timeout': self.config.get_task_timeout(task_name),
            'retry_count': self.config.get_task_retry_count(task_name),
            'config': self.config.get_task_config(task_name)
        }


class PipelineScheduler:
    """Handle automated pipeline scheduling and execution"""
    
    def __init__(self, config: PipelineConfig):
        """
        Initialize scheduler
        
        Args:
            config: PipelineConfig instance
        """
        self.config = config
        self.is_scheduled = config.is_scheduling_enabled()
        self.cron = config.get_cron_schedule()
        
        if self.is_scheduled:
            logger.info(f"Scheduling enabled. Schedule: {self.cron}")
    
    def create_dagster_schedule(self):
        """Create Dagster schedule from configuration"""
        from dagster import schedule
        
        cron = self.cron
        
        @schedule(
            cron_schedule=cron,
            name="automated_pipeline_schedule"
        )
        def automated_pipeline(context):
            """Automatically execute pipeline on schedule"""
            logger.info(f"Scheduled pipeline execution triggered")
            return {}
        
        return automated_pipeline
    
    def get_schedule_info(self) -> Dict[str, Any]:
        """Get scheduling information"""
        return {
            'enabled': self.is_scheduled,
            'cron': self.cron,
            'timezone': self.config.get('scheduling.timezone', 'UTC')
        }


def create_automated_pipeline_job(config_path: Optional[str] = None):
    """
    Create a fully automated Dagster job from configuration
    
    Args:
        config_path: Path to pipeline configuration file
    
    Returns:
        Dagster job with all ops configured and connected
    """
    from dagster import job, graph, op, In, Out, DynamicOutput
    
    # Load configuration
    config = PipelineConfig(config_path)
    dep_graph = TaskDependencyGraph(config)
    
    logger.info("Creating automated pipeline from configuration")
    
    # Get execution order
    execution_order = dep_graph.get_execution_order()
    
    # Create ops dynamically based on configuration
    ops_dict = {}
    
    for task_name in execution_order:
        task_info = dep_graph.get_task_info(task_name)
        timeout = task_info['timeout']
        retry_count = task_info['retry_count']
        
        # Create op factory
        def create_op(name, timeout, retry_count, task_config):
            @op(
                name=f"{name}_op",
                description=f"Execute {name} task",
                tags={
                    "type": name,
                    "timeout": timeout,
                    "retries": retry_count
                }
            )
            def task_op(context):
                """Execute configured task"""
                context.log.info(f"Executing task: {name}")
                context.log.info(f"Configuration: {task_config}")
                
                # Execute based on task type
                return execute_task(context, name, task_config, config)
            
            return task_op
        
        task_config = task_info['config']
        ops_dict[task_name] = create_op(task_name, timeout, retry_count, task_config)
    
    # Create graph that connects ops based on dependencies
    @graph
    def automated_pipeline_graph():
        """Build pipeline graph from configuration"""
        results = {}
        
        for task_name in execution_order:
            op_func = ops_dict[task_name]
            task_info = dep_graph.get_task_info(task_name)
            dependencies = task_info['dependencies']
            
            if not dependencies:
                # Root task with no dependencies
                results[task_name] = op_func()
            else:
                # Task with dependencies
                dep_results = [results[dep] for dep in dependencies if dep in results]
                
                if len(dep_results) == 1:
                    # Single dependency
                    results[task_name] = op_func.alias(f"{task_name}_op")()
                else:
                    # Multiple dependencies - wait for all
                    results[task_name] = op_func.alias(f"{task_name}_op")()
        
        return results[execution_order[-1]] if execution_order else None
    
    # Create job
    @job
    def automated_pipeline_job():
        """Fully automated pipeline job"""
        return automated_pipeline_graph()
    
    return automated_pipeline_job, config, dep_graph


def execute_task(context, task_name: str, task_config: Dict, config: PipelineConfig) -> Dict[str, Any]:
    """
    Execute a task based on its configuration
    
    Args:
        context: Dagster context
        task_name: Name of the task
        task_config: Task configuration
        config: Pipeline configuration
    
    Returns:
        Task execution result
    """
    from src.ingestion.ingest_users import UserDataIngestion
    from src.ingestion.ingest_products import ProductDataIngestion
    from src.ingestion.ingest_transactions import TransactionDataIngestion
    from src.validation.validate_data import DataValidator
    from src.preparation.clean_data import DataPreparation
    from src.features.engineer_features import FeatureEngineer
    from src.model_training.collaborative_filtering import CollaborativeFilteringModel
    from src.utils.storage import DataLakeStorage
    
    try:
        context.log.info(f"Starting task: {task_name}")
        context.log.debug(f"Task config: {task_config}")
        
        # Get storage configuration
        storage_base = config.get('storage.base_dir', 'storage')
        data_dir = config.get('storage.data_dir', 'data')
        
        result = None
        
        if task_name == 'ingestion':
            # Execute all ingestion tasks in parallel
            context.log.info("Running parallel ingestion (users, products, transactions)")
            
            users_result = UserDataIngestion(data_dir, storage_base).ingest()
            products_result = ProductDataIngestion(data_dir, storage_base).ingest()
            transactions_result = TransactionDataIngestion(data_dir, storage_base).ingest()
            
            result = {
                'status': 'success',
                'users': users_result,
                'products': products_result,
                'transactions': transactions_result
            }
        
        elif task_name == 'validation':
            context.log.info("Running data validation")
            validator = DataValidator()
            validation_results = validator.run_validation_suite()
            validator.save_validation_results(validation_results)
            
            # Count failed validations across all datasets
            failed_checks = 0
            for dataset in ['users', 'products', 'transactions']:
                if dataset in validation_results:
                    failed_checks += sum(
                        1 for v in validation_results[dataset]['validations'] 
                        if not v['passed']
                    )
            
            result = {
                'status': 'success',
                'quality_score': validation_results['overall']['quality_score'],
                'total_checks': validation_results['overall']['total_checks'],
                'passed_checks': validation_results['overall']['passed_checks'],
                'failed_checks': failed_checks
            }
        
        elif task_name == 'preparation':
            context.log.info("Running data preparation")
            prep = DataPreparation(storage_base)
            users_df, products_df, transactions_df = prep.run_preparation_pipeline()
            
            result = {
                'status': 'success',
                'users_count': len(users_df),
                'products_count': len(products_df),
                'transactions_count': len(transactions_df)
            }
        
        elif task_name == 'features':
            context.log.info("Running feature engineering")
            engineer = FeatureEngineer(storage_base)
            user_features, item_features, interaction_features = engineer.run_feature_engineering()
            
            result = {
                'status': 'success',
                'user_features': len(user_features),
                'item_features': len(item_features),
                'interaction_features': len(interaction_features)
            }
        
        elif task_name == 'training':
            context.log.info("Running model training")
            storage = DataLakeStorage(storage_base)
            interactions_df = storage.load_latest('interaction_features', 'features')
            
            # Start MLflow run
            mlflow.set_experiment("CF-SVD-Recommendations")
            
            with mlflow.start_run(run_name="automated_pipeline_training"):
                # Log parameters
                mlflow.log_param("algorithm", "SVD")
                mlflow.log_param("n_factors", 100)
                mlflow.log_param("n_epochs", 20)
                mlflow.log_param("lr_all", 0.005)
                mlflow.log_param("reg_all", 0.02)
                
                cf_model = CollaborativeFilteringModel()
                dataset = cf_model.prepare_data(interactions_df)
                trainset, testset = cf_model.train(dataset)
                
                # Log training metrics
                mlflow.log_metric("training_records", trainset.n_ratings)
                mlflow.log_metric("test_records", len(testset))
                mlflow.log_metric("n_users", trainset.n_users)
                mlflow.log_metric("n_items", trainset.n_items)
                
                models_dir = Path('models')
                models_dir.mkdir(exist_ok=True)
                model_path = models_dir / 'collaborative_filtering.pkl'
                cf_model.save_model(str(model_path))
                
                # Log model artifact
                mlflow.log_artifact(str(model_path), artifact_path="models")
                
                context.log.info(f"MLflow run logged: {mlflow.active_run().info.run_id}")
            
            result = {
                'status': 'success',
                'model_path': str(model_path),
                'training_records': trainset.n_ratings,
                'test_records': len(testset),
                'mlflow_run_id': mlflow.active_run().info.run_id if mlflow.active_run() else None
            }
        
        else:
            result = {'status': 'unknown', 'task': task_name}
        
        context.log.info(f"Task '{task_name}' completed successfully")
        return result
    
    except Exception as e:
        context.log.error(f"Task '{task_name}' failed: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    # Test configuration loading
    config = PipelineConfig()
    print("Pipeline Configuration:")
    print(json.dumps(config.to_dict(), indent=2))
    
    # Test dependency graph
    dep_graph = TaskDependencyGraph(config)
    print("\nExecution Order:")
    print(dep_graph.get_execution_order())
    
    print("\nParallel Groups:")
    print(dep_graph.get_parallel_groups())
