"""
Dagster Pipeline Execution Script

Run Dagster pipelines programmatically without the web UI.

Usage:
    python run_dagster_pipeline.py                  # Run complete pipeline
    python run_dagster_pipeline.py --ingestion-only # Run ingestion only
    python run_dagster_pipeline.py --ui             # Start web UI
"""

import sys
from pathlib import Path
from datetime import datetime
import argparse

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from dagster import execute_job, DagsterInstance
from src.orchestration.dagster_pipeline import (
    complete_pipeline_job,
    ingestion_job
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


def print_header(title):
    """Print formatted header"""
    print("\n" + "="*80)
    print(f"▶ {title}")
    print("="*80)


def print_summary(result):
    """Print execution summary"""
    print("\n" + "="*80)
    print("EXECUTION SUMMARY")
    print("="*80)
    
    if result.success:
        print("✓ Pipeline executed successfully!")
        print(f"  Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("✗ Pipeline execution failed!")
        print(f"  Failed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\nEvent Summary:")
    print(f"  Total events: {len(result.all_events)}")
    
    # Count event types
    started = sum(1 for e in result.all_events if 'STARTED' in str(e.event_type))
    succeeded = sum(1 for e in result.all_events if 'SUCCESS' in str(e.event_type))
    failed = sum(1 for e in result.all_events if 'FAILURE' in str(e.event_type))
    
    print(f"  Started: {started}")
    print(f"  Succeeded: {succeeded}")
    print(f"  Failed: {failed}")
    
    print("\n" + "="*80)


def run_complete_pipeline():
    """Run the complete end-to-end pipeline"""
    print_header("Running Complete Pipeline (Ingestion → Validation → Prep → Features → Training)")
    
    logger.info("Starting complete pipeline execution via Dagster")
    
    try:
        # Create Dagster instance
        instance = DagsterInstance.ephemeral()
        
        # Execute job
        result = execute_job(
            complete_pipeline_job,
            instance=instance,
            raise_on_error=False
        )
        
        # Print summary
        print_summary(result)
        
        return result.success
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}", exc_info=True)
        print(f"\n✗ Error: {str(e)}")
        return False


def run_ingestion_only():
    """Run ingestion pipeline only"""
    print_header("Running Ingestion Pipeline Only")
    
    logger.info("Starting ingestion pipeline execution via Dagster")
    
    try:
        # Create Dagster instance
        instance = DagsterInstance.ephemeral()
        
        # Execute job
        result = execute_job(
            ingestion_job,
            instance=instance,
            raise_on_error=False
        )
        
        # Print summary
        print_summary(result)
        
        return result.success
        
    except Exception as e:
        logger.error(f"Ingestion execution failed: {str(e)}", exc_info=True)
        print(f"\n✗ Error: {str(e)}")
        return False


def start_ui():
    """Start Dagster web UI"""
    print_header("Starting Dagster Web UI")
    
    import subprocess
    
    print("Starting Dagster development server...")
    print("Web UI will be available at: http://localhost:3000")
    print("Press Ctrl+C to stop\n")
    
    try:
        subprocess.run("dagster dev", shell=True, cwd=Path(__file__).parent)
    except KeyboardInterrupt:
        print("\n\nDagster UI stopped")
        return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Execute Dagster pipelines for RecoMart data engineering",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_dagster_pipeline.py                    # Run complete pipeline
  python run_dagster_pipeline.py --ingestion-only   # Ingestion only
  python run_dagster_pipeline.py --ui               # Start web UI
        """
    )
    
    parser.add_argument(
        '--ingestion-only',
        action='store_true',
        help='Run ingestion pipeline only'
    )
    parser.add_argument(
        '--ui',
        action='store_true',
        help='Start Dagster web UI'
    )
    parser.add_argument(
        '--version',
        action='store_true',
        help='Show Dagster version'
    )
    
    args = parser.parse_args()
    
    if args.version:
        import dagster
        print(f"Dagster version: {dagster.__version__}")
        return True
    
    if args.ui:
        return start_ui()
    
    if args.ingestion_only:
        return run_ingestion_only()
    
    # Default: run complete pipeline
    return run_complete_pipeline()


if __name__ == "__main__":
    print("\n╔" + "═"*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "RECOMART DAGSTER PIPELINE EXECUTOR".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "═"*78 + "╝")
    
    success = main()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
