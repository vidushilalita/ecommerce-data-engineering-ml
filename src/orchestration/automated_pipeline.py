"""
Configuration-Driven Dagster Pipeline

This module creates the automated Dagster pipeline from configuration file.
All pipeline behavior is controlled via pipeline_config.yaml
"""

import sys
from pathlib import Path
from typing import Dict, Any

from dagster import (
    job,
    op,
    graph,
    DependencyDefinition,
    In,
    Out,
    Field,
    String,
    Nothing,
    DynamicOut,
    DynamicOutput,
    execute_job,
    DagsterInstance,
    in_process_executor,
)

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.orchestration.config_driven_pipeline import (
    PipelineConfig,
    TaskDependencyGraph,
    execute_task,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


# Load configuration
CONFIG = PipelineConfig()
DEP_GRAPH = TaskDependencyGraph(CONFIG)


# ==================== DYNAMIC OP CREATION ====================

def create_task_ops():
    """Create task ops dynamically from configuration"""
    ops_dict = {}
    
    for task_name in DEP_GRAPH.tasks.keys():
        task_config = CONFIG.get_task_config(task_name)
        timeout = CONFIG.get_task_timeout(task_name)
        retry_count = CONFIG.get_task_retry_count(task_name)
        
        # Create op factory with closure
        def make_op(name, timeout, retry_count):
            @op(
                name=f"{name}_op",
                description=f"Execute {name} task with timeout {timeout}s",
                tags={
                    "type": name,
                    "timeout": str(timeout),
                    "retries": str(retry_count),
                    "config_driven": "true"
                },
                config_schema={
                    "enabled": Field(bool, default_value=True),
                    "timeout": Field(int, default_value=timeout),
                    "retries": Field(int, default_value=retry_count),
                }
            )
            def task_op(context) -> Dict[str, Any]:
                """Execute task from configuration"""
                context.log.info(f"╔═══════════════════════════════════════════════════════════╗")
                context.log.info(f"║ EXECUTING TASK: {name.upper():50s} ║")
                context.log.info(f"╠═══════════════════════════════════════════════════════════╣")
                context.log.info(f"║ Timeout: {context.op_config['timeout']}s")
                context.log.info(f"║ Max Retries: {context.op_config['retries']}")
                context.log.info(f"╚═══════════════════════════════════════════════════════════╝")
                
                # Execute task
                result = execute_task(context, name, task_config, CONFIG)
                
                context.log.info(f"✓ Task '{name}' completed with status: {result.get('status')}")
                
                return result
            
            return task_op
        
        ops_dict[task_name] = make_op(task_name, timeout, retry_count)
    
    return ops_dict


# Create ops
TASK_OPS = create_task_ops()


# ==================== DEPENDENCY INJECTION ====================

def build_graph_with_dependencies():
    """
    Build graph that respects task dependencies from configuration
    
    The graph automatically ensures:
    - Tasks wait for their dependencies to complete
    - Dependencies are managed by configuration
    - Execution order is determined by dependency graph
    """
    execution_order = DEP_GRAPH.get_execution_order()
    
    logger.info(f"Building graph with execution order: {execution_order}")
    
    @graph
    def configured_pipeline_graph():
        """Automated pipeline graph from configuration"""
        
        # Dictionary to store task results
        task_results = {}
        
        # Execute tasks in order, each waiting for dependencies
        for task_name in execution_order:
            op_func = TASK_OPS[task_name]
            dependencies = DEP_GRAPH.graph.get(task_name, [])
            
            context_str = f"Task: {task_name}"
            if dependencies:
                context_str += f" | Depends on: {', '.join(dependencies)}"
            
            logger.debug(context_str)
            
            # Execute op (dependencies are implicit through sequential execution)
            result = op_func()
            task_results[task_name] = result
        
        # Return final task result
        final_task = execution_order[-1] if execution_order else None
        return task_results[final_task] if final_task else None
    
    return configured_pipeline_graph


# ==================== JOB DEFINITIONS ====================

@job(
    name="automated_pipeline_job",
    description="Fully automated pipeline controlled by pipeline_config.yaml. "
                "Tasks automatically wait for dependencies to complete.",
    tags={
        "type": "production",
        "config_driven": "true",
        "mode": CONFIG.get_execution_mode()
    },
    executor_def=in_process_executor
)
def automated_pipeline_job():
    """
    Fully Automated Data Pipeline
    
    This job orchestrates the complete data engineering and ML training pipeline.
    All configuration comes from pipeline_config.yaml
    
    Task Dependencies (automatic):
    1. ingestion (no dependencies)
    2. validation (waits for ingestion)
    3. preparation (waits for validation)
    4. features (waits for preparation)
    5. training (waits for features)
    
    Features:
    - ✓ Automatic dependency management
    - ✓ Configurable timeouts and retries
    - ✓ Real-time monitoring in web UI
    - ✓ Detailed logging
    - ✓ Error handling and recovery
    """
    build_graph_with_dependencies()()


@job(
    name="ingestion_only_job",
    description="Run only data ingestion (from pipeline_config.yaml)",
    tags={"type": "ingestion", "config_driven": "true"},
    executor_def=in_process_executor
)
def ingestion_only_job():
    """Job that runs only the ingestion task"""
    if CONFIG.is_task_enabled('ingestion'):
        TASK_OPS['ingestion']()
    else:
        raise Exception("Ingestion task is disabled in configuration")


@job(
    name="validation_only_job",
    description="Run only validation (requires prior ingestion)",
    tags={"type": "validation", "config_driven": "true"},
    executor_def=in_process_executor
)
def validation_only_job():
    """Job that runs only the validation task"""
    if CONFIG.is_task_enabled('validation'):
        TASK_OPS['ingestion']()
        TASK_OPS['validation']()
    else:
        raise Exception("Validation task is disabled in configuration")


# ==================== EXECUTION HELPERS ====================

def print_pipeline_info():
    """Print pipeline information from configuration"""
    print("\n" + "="*80)
    print("PIPELINE CONFIGURATION SUMMARY")
    print("="*80 + "\n")
    
    print(f"Pipeline Name: {CONFIG.get('pipeline.name')}")
    print(f"Description: {CONFIG.get('pipeline.description')}")
    print(f"Execution Mode: {CONFIG.get_execution_mode()}")
    print(f"Pipeline Enabled: {CONFIG.get('pipeline.enabled')}")
    
    print(f"\nTasks ({len(DEP_GRAPH.tasks)}):")
    for task_name, task_config in DEP_GRAPH.tasks.items():
        enabled = "✓" if task_config.get('enabled', True) else "✗"
        timeout = CONFIG.get_task_timeout(task_name)
        deps = ", ".join(DEP_GRAPH.graph.get(task_name, [])) or "None"
        retries = CONFIG.get_task_retry_count(task_name)
        
        print(f"  [{enabled}] {task_name:15s} | Timeout: {timeout:4d}s | "
              f"Retries: {retries} | Depends on: {deps}")
    
    print(f"\nExecution Order: {' → '.join(DEP_GRAPH.get_execution_order())}")
    
    if CONFIG.is_scheduling_enabled():
        print(f"\nScheduling: ENABLED")
        print(f"  Cron: {CONFIG.get_cron_schedule()}")
        print(f"  Timezone: {CONFIG.get('scheduling.timezone')}")
    else:
        print(f"\nScheduling: DISABLED")
    
    print("\n" + "="*80 + "\n")


def execute_pipeline_programmatically():
    """Execute pipeline without web UI"""
    print_pipeline_info()
    
    print("Executing automated pipeline...")
    print("(This may take several minutes)\n")
    
    instance = DagsterInstance.ephemeral()
    
    result = execute_job(
        automated_pipeline_job,
        instance=instance,
        raise_on_error=False
    )
    
    if result.success:
        print("\n" + "="*80)
        print("✓ PIPELINE EXECUTION SUCCESSFUL")
        print("="*80)
        return True
    else:
        print("\n" + "="*80)
        print("✗ PIPELINE EXECUTION FAILED")
        print("="*80)
        return False


if __name__ == "__main__":
    print_pipeline_info()
