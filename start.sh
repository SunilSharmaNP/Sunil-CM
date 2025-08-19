#!/bin/bash

# Enhanced MERGE-BOT Startup Script
# Combines functionality from both repositories with improvements

set -e  # Exit on any error

# ===== CONSTANTS =====
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="logs/startup.log"
PID_FILE="bot.pid"
VENV_PATH="venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ===== LOGGING FUNCTIONS =====
log() {
    echo -e "${CYAN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

log_debug() {
    if [ "$DEBUG_MODE" = "true" ]; then
        echo -e "${PURPLE}[DEBUG]${NC} $1" | tee -a "$LOG_FILE"
    fi
}

# ===== BANNER =====
print_banner() {
    echo -e "${BLUE}"
    cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                    ENHANCED MERGE-BOT v6.0                   ║
║               Advanced Telegram Video Merger                 ║
╠═══════════════════════════════════════════════════════════════╣
║  🎯 Rich UI (yashoswalyo) + Modern Core (SunilSharmaNP)     ║
║  🚀 Smart Downloads • Robust Merging • GoFile Integration    ║
║  📊 Progress Tracking • Error Recovery • Premium Support     ║
╚═══════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

# ===== UTILITY FUNCTIONS =====
check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "Required command '$1' is not installed"
        return 1
    fi
    return 0
}

check_file() {
    if [ ! -f "$1" ]; then
        log_error "Required file '$1' not found"
        return 1
    fi
    return 0
}

create_directory() {
    if [ ! -d "$1" ]; then
        mkdir -p "$1"
        log_info "Created directory: $1"
    fi
}

# ===== SYSTEM CHECKS =====
check_system_requirements() {
    log_info "Checking system requirements..."
    
    # Check Python version
    if check_command python3; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
        log_info "Python version: $PYTHON_VERSION"
        
        # Check if Python version is >= 3.8
        if python3 -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)"; then
            log_info "✅ Python version is supported"
        else
            log_error "❌ Python 3.8+ is required, found $PYTHON_VERSION"
            return 1
        fi
    else
        log_error "❌ Python 3 is not installed"
        return 1
    fi
    
    # Check FFmpeg
    if check_command ffmpeg; then
        FFMPEG_VERSION=$(ffmpeg -version 2>&1 | head -n1 | cut -d' ' -f3)
        log_info "✅ FFmpeg version: $FFMPEG_VERSION"
    else
        log_error "❌ FFmpeg is not installed"
        log_info "Install FFmpeg with:"
        log_info "  Ubuntu/Debian: sudo apt-get install ffmpeg"
        log_info "  CentOS/RHEL: sudo yum install ffmpeg"
        log_info "  macOS: brew install ffmpeg"
        return 1
    fi
    
    # Check disk space
    AVAILABLE_SPACE=$(df . | tail -1 | awk '{print $4}')
    if [ "$AVAILABLE_SPACE" -lt 1048576 ]; then  # Less than 1GB
        log_warn "⚠️ Low disk space: $(df -h . | tail -1 | awk '{print $4}') available"
    else
        log_info "✅ Disk space: $(df -h . | tail -1 | awk '{print $4}') available"
    fi
    
    return 0
}

# ===== PYTHON ENVIRONMENT SETUP =====
setup_python_environment() {
    log_info "Setting up Python environment..."
    
    # Check if virtual environment should be used
    if [ "$USE_VENV" = "true" ] || [ -f "$VENV_PATH/bin/activate" ]; then
        if [ ! -d "$VENV_PATH" ]; then
            log_info "Creating virtual environment..."
            python3 -m venv "$VENV_PATH"
        fi
        
        log_info "Activating virtual environment..."
        source "$VENV_PATH/bin/activate"
        
        # Upgrade pip in venv
        pip install --upgrade pip setuptools wheel
        log_info "✅ Virtual environment activated"
    else
        log_info "Using system Python environment"
    fi
    
    # Check if requirements need to be installed
    if [ ! -f "requirements_installed.flag" ] || [ "requirements.txt" -nt "requirements_installed.flag" ]; then
        log_info "Installing/updating Python dependencies..."
        
        if pip install -r requirements.txt --upgrade; then
            touch requirements_installed.flag
            log_info "✅ Dependencies installed successfully"
        else
            log_error "❌ Failed to install dependencies"
            return 1
        fi
    else
        log_info "✅ Dependencies are up to date"
    fi
    
    return 0
}

# ===== CONFIGURATION VALIDATION =====
validate_configuration() {
    log_info "Validating configuration..."
    
    # Check for config files
    CONFIG_FOUND=false
    
    if [ -f "config.env" ]; then
        log_info "✅ Found config.env file"
        CONFIG_FOUND=true
        
        # Load environment variables
        set -a  # Export all variables
        source config.env
        set +a
        
    elif [ -f ".env" ]; then
        log_info "✅ Found .env file"
        CONFIG_FOUND=true
        
        set -a
        source .env
        set +a
        
    else
        log_warn "⚠️ No config file found, using environment variables"
    fi
    
    # Check required variables
    REQUIRED_VARS=("API_ID" "API_HASH" "BOT_TOKEN" "OWNER" "PASSWORD")
    MISSING_VARS=()
    
    for var in "${REQUIRED_VARS[@]}"; do
        if [ -z "${!var}" ] && [ -z "${!var// }" ]; then
            MISSING_VARS+=("$var")
        fi
    done
    
    # Also check TELEGRAM_API as alternative to API_ID
    if [ -z "$API_ID" ] && [ -n "$TELEGRAM_API" ]; then
        export API_ID="$TELEGRAM_API"
        log_info "Using TELEGRAM_API as API_ID"
    fi
    
    if [ ${#MISSING_VARS[@]} -ne 0 ]; then
        log_error "❌ Missing required configuration variables:"
        for var in "${MISSING_VARS[@]}"; do
            log_error "   - $var"
        done
        log_error ""
        log_error "Please set these variables in config.env or as environment variables"
        return 1
    fi
    
    log_info "✅ Configuration validation passed"
    return 0
}

# ===== DIRECTORY SETUP =====
setup_directories() {
    log_info "Setting up directories..."
    
    DIRECTORIES=("downloads" "logs" "temp" "cache" "backups")
    
    for dir in "${DIRECTORIES[@]}"; do
        create_directory "$dir"
    done
    
    # Set proper permissions
    chmod 755 downloads logs temp cache backups 2>/dev/null || true
    
    log_info "✅ Directories ready"
}

# ===== BOT STARTUP =====
start_bot() {
    log_info "Starting Enhanced MERGE-BOT..."
    
    # Check if bot is already running
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if kill -0 "$OLD_PID" 2>/dev/null; then
            log_warn "Bot is already running with PID $OLD_PID"
            read -p "Stop and restart? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                kill "$OLD_PID" 2>/dev/null || true
                sleep 2
                log_info "Stopped old bot process"
            else
                log_info "Exiting without starting new instance"
                exit 0
            fi
        fi
    fi
    
    # Load configuration if get_config.py exists
    if [ -f "get_config.py" ]; then
        log_info "Loading dynamic configuration..."
        if python3 get_config.py; then
            log_info "✅ Dynamic configuration loaded"
        else
            log_warn "⚠️ Dynamic configuration failed, using static config"
        fi
    fi
    
    # Start the bot
    log_info "🚀 Launching Enhanced MERGE-BOT v6.0..."
    
    # Run bot with proper error handling
    if python3 bot.py; then
        log_info "✅ Bot started successfully"
    else
        EXIT_CODE=$?
        log_error "❌ Bot failed to start (exit code: $EXIT_CODE)"
        return $EXIT_CODE
    fi
}

# ===== SIGNAL HANDLERS =====
cleanup_on_exit() {
    log_info "Received shutdown signal, cleaning up..."
    
    if [ -f "$PID_FILE" ]; then
        rm -f "$PID_FILE"
    fi
    
    log_info "👋 Enhanced MERGE-BOT shutdown complete"
    exit 0
}

# ===== MAIN FUNCTION =====
main() {
    # Set up signal handlers
    trap cleanup_on_exit SIGINT SIGTERM
    
    # Create logs directory first
    mkdir -p logs
    
    # Print banner
    print_banner
    
    # Store bot PID
    echo $$ > "$PID_FILE"
    
    log_info "Enhanced MERGE-BOT v6.0 startup initiated"
    log_info "Script directory: $SCRIPT_DIR"
    log_info "Process ID: $$"
    
    # Run initialization steps
    if ! check_system_requirements; then
        log_error "❌ System requirements check failed"
        exit 1
    fi
    
    if ! setup_python_environment; then
        log_error "❌ Python environment setup failed"
        exit 1
    fi
    
    if ! validate_configuration; then
        log_error "❌ Configuration validation failed"
        exit 1
    fi
    
    setup_directories
    
    # Start the bot
    if start_bot; then
        log_info "🎉 Enhanced MERGE-BOT started successfully!"
    else
        log_error "💥 Failed to start Enhanced MERGE-BOT"
        exit 1
    fi
    
    # Cleanup on normal exit
    cleanup_on_exit
}

# ===== COMMAND LINE ARGUMENTS =====
case "${1:-start}" in
    start)
        main
        ;;
    stop)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if kill -0 "$PID" 2>/dev/null; then
                kill "$PID"
                log_info "Bot stopped (PID: $PID)"
            else
                log_warn "Bot is not running"
            fi
            rm -f "$PID_FILE"
        else
            log_warn "No PID file found, bot may not be running"
        fi
        ;;
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    status)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if kill -0 "$PID" 2>/dev/null; then
                log_info "Bot is running (PID: $PID)"
            else
                log_warn "Bot is not running (stale PID file)"
            fi
        else
            log_info "Bot is not running"
        fi
        ;;
    logs)
        if [ -f "$LOG_FILE" ]; then
            tail -f "$LOG_FILE"
        else
            log_error "Log file not found"
        fi
        ;;
    clean)
        log_info "Cleanup completed"
        ;;
    install)
        check_system_requirements
        setup_python_environment
        setup_directories
        log_info "Installation completed"
        ;;
    *)
        echo "Enhanced MERGE-BOT Control Script"
        echo "Usage: $0 {start|stop|restart|status|logs|clean|install}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the bot (default)"
        echo "  stop     - Stop the bot"
        echo "  restart  - Restart the bot"
        echo "  status   - Check bot status"
        echo "  logs     - View live logs"
        echo "  clean    - Clean temporary files"
        echo "  install  - Install dependencies and setup"
        exit 1
        ;;
esac
