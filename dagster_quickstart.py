"""
Quick Start Script for Dagster Pipeline

This script provides easy commands to:
1. Install dependencies
2. Start the Dagster web UI
3. Execute pipelines
4. Check status
"""

import subprocess
import sys
import os
from pathlib import Path


class DagsterQuickStart:
    """Helper class for Dagster operations"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.python_exe = sys.executable
    
    def run_command(self, cmd, description):
        """Run a shell command and handle output"""
        print(f"\n{'='*70}")
        print(f"▶ {description}")
        print(f"{'='*70}")
        print(f"Command: {cmd}\n")
        
        try:
            result = subprocess.run(cmd, shell=True, cwd=self.project_root)
            if result.returncode == 0:
                print(f"\n✓ {description} completed successfully!")
                return True
            else:
                print(f"\n✗ {description} failed with code {result.returncode}")
                return False
        except Exception as e:
            print(f"\n✗ Error: {str(e)}")
            return False
    
    def install_dependencies(self):
        """Install required packages"""
        cmd = f"{self.python_exe} -m pip install -r requirements.txt"
        return self.run_command(cmd, "Installing dependencies")
    
    def start_ui(self, port=3000):
        """Start Dagster web UI"""
        cmd = f"dagster dev --port {port}"
        print(f"\n{'='*70}")
        print("▶ Starting Dagster Web UI")
        print(f"{'='*70}")
        print(f"Dagster UI will be available at: http://localhost:{port}")
        print("Press Ctrl+C to stop the server\n")
        
        try:
            os.chdir(self.project_root)
            subprocess.run(cmd, shell=True)
        except KeyboardInterrupt:
            print("\n\nDagster UI stopped")
            return True
    
    def run_ingestion_job(self):
        """Run ingestion job via CLI"""
        cmd = f'{self.python_exe} -m dagster job execute -f src/orchestration/dagster_pipeline.py -j ingestion_job'
        return self.run_command(cmd, "Running Ingestion Job")
    
    def run_complete_pipeline(self):
        """Run complete pipeline via CLI"""
        cmd = f'{self.python_exe} -m dagster job execute -f src/orchestration/dagster_pipeline.py -j complete_pipeline_job'
        return self.run_command(cmd, "Running Complete Pipeline")
    
    def check_dagster_version(self):
        """Check installed Dagster version"""
        cmd = f"{self.python_exe} -m dagster --version"
        print(f"\nChecking Dagster installation...")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ {result.stdout.strip()}")
            return True
        else:
            print("✗ Dagster not found. Please run: pip install dagster dagster-webui")
            return False
    
    def show_menu(self):
        """Display interactive menu"""
        print("\n" + "="*70)
        print("RECOMART DAGSTER PIPELINE - QUICK START")
        print("="*70)
        print("\nAvailable Commands:")
        print("  1. Check Dependencies      - Verify Dagster installation")
        print("  2. Install Dependencies    - Install all required packages")
        print("  3. Start Web UI            - Launch Dagster web interface (http://localhost:3000)")
        print("  4. Run Ingestion Only      - Execute data ingestion pipeline")
        print("  5. Run Complete Pipeline   - Execute full end-to-end pipeline")
        print("  6. Exit                    - Close this menu")
        print("\n" + "="*70)
    
    def interactive_menu(self):
        """Run interactive menu"""
        while True:
            self.show_menu()
            choice = input("\nEnter your choice (1-6): ").strip()
            
            if choice == '1':
                self.check_dagster_version()
            elif choice == '2':
                if self.install_dependencies():
                    self.check_dagster_version()
            elif choice == '3':
                self.start_ui()
            elif choice == '4':
                if self.run_ingestion_job():
                    input("\nPress Enter to continue...")
            elif choice == '5':
                if self.run_complete_pipeline():
                    input("\nPress Enter to continue...")
            elif choice == '6':
                print("\nGoodbye!")
                break
            else:
                print("\n✗ Invalid choice. Please select 1-6")


def print_quick_start():
    """Print quick start instructions"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DAGSTER PIPELINE QUICK START GUIDE                        ║
╚══════════════════════════════════════════════════════════════════════════════╝

📋 INSTALLATION
────────────────────────────────────────────────────────────────────────────────
1. Install dependencies:
   pip install -r requirements.txt

2. Verify Dagster:
   dagster --version

🚀 RUNNING THE PIPELINE
────────────────────────────────────────────────────────────────────────────────

OPTION A: Web UI (Recommended)
   dagster dev
   → Opens http://localhost:3000 in your browser
   → Click job name → Click "Materialize" to run

OPTION B: Command Line
   # Run ingestion only
   dagster job execute -f src/orchestration/dagster_pipeline.py -j ingestion_job
   
   # Run complete pipeline
   dagster job execute -f src/orchestration/dagster_pipeline.py -j complete_pipeline_job

OPTION C: Python Script
   python run_dagster_pipeline.py

📊 MONITORING
────────────────────────────────────────────────────────────────────────────────
• Web UI: http://localhost:3000 (recommended)
• Logs: dagster_data/logs/
• Outputs: storage/ (data lake) and models/ (trained models)

📖 DETAILED DOCUMENTATION
────────────────────────────────────────────────────────────────────────────────
See: docs/DAGSTER_ORCHESTRATION.md

""")


if __name__ == "__main__":
    # Check if running with argument
    if len(sys.argv) > 1:
        quickstart = DagsterQuickStart()
        
        if sys.argv[1] == '--help':
            print_quick_start()
        elif sys.argv[1] == 'install':
            quickstart.install_dependencies()
        elif sys.argv[1] == 'ui':
            quickstart.start_ui()
        elif sys.argv[1] == 'check':
            quickstart.check_dagster_version()
        elif sys.argv[1] == 'ingestion':
            quickstart.run_ingestion_job()
        elif sys.argv[1] == 'complete':
            quickstart.run_complete_pipeline()
        else:
            print(f"Unknown command: {sys.argv[1]}")
            print_quick_start()
    else:
        # Run interactive menu
        quickstart = DagsterQuickStart()
        quickstart.interactive_menu()
