#!/bin/bash

################################################################################
# Dagster Pipeline Control Script for Linux/macOS
################################################################################
#
# Usage:
#   ./run_pipeline.sh                    - Start Dagster Web UI
#   ./run_pipeline.sh install            - Install dependencies
#   ./run_pipeline.sh ingestion          - Run ingestion only
#   ./run_pipeline.sh complete           - Run complete pipeline
#   ./run_pipeline.sh help               - Show help
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get project root
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Print header
print_header() {
    echo ""
    echo "============================================================================"
    echo "$1"
    echo "============================================================================"
    echo ""
}

# Print info
print_info() {
    echo -e "${GREEN}▶${NC} $1"
}

# Print error
print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Print success
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Show help
show_help() {
    print_header "RECOMART DAGSTER PIPELINE - LINUX/MACOS HELP"
    
    echo "Usage: ./run_pipeline.sh [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  (none)      - Show interactive menu"
    echo "  install     - Install dependencies (pip install -r requirements.txt)"
    echo "  ui          - Start Dagster Web UI (http://localhost:3000)"
    echo "  ingestion   - Run data ingestion pipeline"
    echo "  complete    - Run complete end-to-end pipeline"
    echo "  check       - Check Dagster installation"
    echo "  help        - Show this help message"
    echo ""
    echo "Quick Start:"
    echo "  1. chmod +x run_pipeline.sh"
    echo "  2. ./run_pipeline.sh install"
    echo "  3. ./run_pipeline.sh ui"
    echo "  4. Open http://localhost:3000"
    echo ""
    echo "For detailed docs: see docs/DAGSTER_QUICKSTART.md"
    echo "============================================================================"
    echo ""
}

# Show menu
show_menu() {
    print_header "RECOMART DAGSTER PIPELINE - INTERACTIVE MENU"
    
    echo "1. Start Web UI (recommended)"
    echo "2. Install Dependencies"
    echo "3. Run Ingestion Only"
    echo "4. Run Complete Pipeline"
    echo "5. Check Installation"
    echo "6. Show Help"
    echo "7. Exit"
    echo ""
    read -p "Enter your choice (1-7): " choice
    
    case $choice in
        1) cmd_ui ;;
        2) cmd_install ;;
        3) cmd_ingestion ;;
        4) cmd_complete ;;
        5) cmd_check ;;
        6) show_help ;;
        7) exit 0 ;;
        *) 
            print_error "Invalid choice. Please select 1-7."
            show_menu
            ;;
    esac
}

# Check installation
cmd_check() {
    echo ""
    echo "Checking Dagster installation..."
    
    if python3 -m dagster --version >/dev/null 2>&1; then
        version=$(python3 -m dagster --version)
        print_success "Dagster is installed: $version"
    else
        print_error "Dagster not found. Run: ./run_pipeline.sh install"
        exit 1
    fi
}

# Install dependencies
cmd_install() {
    print_header "Installing Dependencies"
    
    cd "$PROJECT_ROOT"
    
    if ! command -v pip &> /dev/null; then
        print_error "pip not found. Please install Python 3 and pip."
        exit 1
    fi
    
    print_info "Installing packages from requirements.txt..."
    pip install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        print_success "Installation complete!"
        echo ""
        echo "Next steps:"
        echo "  1. ./run_pipeline.sh ui"
        echo "  2. Open http://localhost:3000"
    else
        print_error "Installation failed"
        exit 1
    fi
}

# Start Web UI
cmd_ui() {
    print_header "Starting Dagster Web UI"
    
    echo -e "Web UI will be available at: ${BLUE}http://localhost:3000${NC}"
    echo "Press Ctrl+C to stop"
    echo ""
    
    cd "$PROJECT_ROOT"
    dagster dev
}

# Run ingestion only
cmd_ingestion() {
    print_header "Running Data Ingestion Pipeline"
    
    cd "$PROJECT_ROOT"
    
    print_info "Executing ingestion job..."
    python3 -m dagster job execute \
        -f src/orchestration/dagster_pipeline.py \
        -j ingestion_job
    
    print_success "Pipeline completed"
}

# Run complete pipeline
cmd_complete() {
    print_header "Running Complete End-to-End Pipeline"
    
    cd "$PROJECT_ROOT"
    
    echo "This may take 10-15 seconds..."
    echo ""
    
    print_info "Executing complete pipeline..."
    python3 -m dagster job execute \
        -f src/orchestration/dagster_pipeline.py \
        -j complete_pipeline_job
    
    print_success "Pipeline completed"
}

# Main
main() {
    # Make sure we're in the project root
    cd "$PROJECT_ROOT"
    
    # Handle commands
    case "${1:-}" in
        help)
            show_help
            ;;
        install)
            cmd_install
            ;;
        ui)
            cmd_ui
            ;;
        ingestion)
            cmd_ingestion
            ;;
        complete)
            cmd_complete
            ;;
        check)
            cmd_check
            ;;
        "")
            show_menu
            ;;
        *)
            print_error "Unknown command: '$1'"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Make script executable
if [ ! -x "$0" ]; then
    chmod +x "$0"
    echo "Script made executable"
fi

# Run main
main "$@"
