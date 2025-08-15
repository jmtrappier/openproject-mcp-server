#!/bin/bash
# Deployment script for OpenProject MCP Server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="openproject-mcp-server"
CONTAINER_NAME="openproject-mcp-server"
DEFAULT_PORT=8080

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi
}

check_env_file() {
    if [ ! -f ".env" ]; then
        log_warn ".env file not found. Creating from .env.example..."
        if [ -f "env.example" ]; then
            cp env.example .env
            log_warn "Please edit .env file with your OpenProject configuration before running."
            return 1
        else
            log_error "No .env.example file found. Please create .env manually."
            return 1
        fi
    fi
    
    # Check required variables
    if ! grep -q "OPENPROJECT_URL=" .env || ! grep -q "OPENPROJECT_API_KEY=" .env; then
        log_error "Missing required environment variables in .env file:"
        log_error "  - OPENPROJECT_URL"
        log_error "  - OPENPROJECT_API_KEY"
        return 1
    fi
    
    return 0
}

build_image() {
    log_info "Building Docker image..."
    docker build -t $IMAGE_NAME .
    log_info "Docker image built successfully"
}

stop_existing() {
    if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
        log_info "Stopping existing container..."
        docker stop $CONTAINER_NAME
    fi
    
    if docker ps -a -q -f name=$CONTAINER_NAME | grep -q .; then
        log_info "Removing existing container..."
        docker rm $CONTAINER_NAME
    fi
}

run_container() {
    local port=${1:-$DEFAULT_PORT}
    
    log_info "Starting container on port $port..."
    
    docker run -d \
        --name $CONTAINER_NAME \
        --env-file .env \
        -p $port:8080 \
        -v "$(pwd)/logs:/app/logs" \
        -v "$(pwd)/data:/app/data" \
        --restart unless-stopped \
        $IMAGE_NAME
    
    log_info "Container started successfully"
    log_info "Server available at: http://localhost:$port"
}

show_logs() {
    log_info "Showing container logs (Ctrl+C to stop):"
    docker logs -f $CONTAINER_NAME
}

show_status() {
    if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
        log_info "Container is running"
        docker ps -f name=$CONTAINER_NAME
        echo
        log_info "Recent logs:"
        docker logs --tail 10 $CONTAINER_NAME
    else
        log_warn "Container is not running"
    fi
}

# Main deployment function
deploy() {
    local port=${1:-$DEFAULT_PORT}
    
    log_info "Starting OpenProject MCP Server deployment..."
    
    check_docker
    
    if ! check_env_file; then
        log_error "Environment configuration incomplete. Please fix and try again."
        exit 1
    fi
    
    build_image
    stop_existing
    run_container $port
    
    # Wait a moment for startup
    sleep 3
    
    # Check if container is still running
    if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
        log_info "Deployment completed successfully!"
        log_info "Run './scripts/deploy.sh logs' to view logs"
        log_info "Run './scripts/deploy.sh status' to check status"
    else
        log_error "Container failed to start. Check logs with: docker logs $CONTAINER_NAME"
        exit 1
    fi
}

# Command handling
case "${1:-deploy}" in
    "deploy")
        deploy $2
        ;;
    "build")
        check_docker
        build_image
        ;;
    "start")
        check_docker
        if ! check_env_file; then
            exit 1
        fi
        run_container $2
        ;;
    "stop")
        check_docker
        if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
            log_info "Stopping container..."
            docker stop $CONTAINER_NAME
            log_info "Container stopped"
        else
            log_warn "Container is not running"
        fi
        ;;
    "restart")
        check_docker
        if ! check_env_file; then
            exit 1
        fi
        stop_existing
        run_container $2
        ;;
    "logs")
        check_docker
        show_logs
        ;;
    "status")
        check_docker
        show_status
        ;;
    "clean")
        check_docker
        stop_existing
        if docker images -q $IMAGE_NAME | grep -q .; then
            log_info "Removing Docker image..."
            docker rmi $IMAGE_NAME
        fi
        log_info "Cleanup completed"
        ;;
    "help")
        echo "OpenProject MCP Server Deployment Script"
        echo
        echo "Usage: $0 [command] [port]"
        echo
        echo "Commands:"
        echo "  deploy [port]  - Build and deploy the server (default: port 8080)"
        echo "  build          - Build Docker image only"
        echo "  start [port]   - Start container (default: port 8080)"
        echo "  stop           - Stop container"
        echo "  restart [port] - Restart container"
        echo "  logs           - Show container logs"
        echo "  status         - Show container status"
        echo "  clean          - Stop container and remove image"
        echo "  help           - Show this help"
        echo
        echo "Examples:"
        echo "  $0 deploy         # Deploy on default port 8080"
        echo "  $0 deploy 9000    # Deploy on port 9000"
        echo "  $0 logs           # View logs"
        echo "  $0 status         # Check status"
        ;;
    *)
        log_error "Unknown command: $1"
        log_info "Run '$0 help' for usage information"
        exit 1
        ;;
esac



