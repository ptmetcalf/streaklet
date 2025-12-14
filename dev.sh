#!/bin/bash
# Development helper script

case "$1" in
    "test")
        echo "Running tests..."
        python -m pytest tests/ -v
        ;;
    "test-cov")
        echo "Running tests with coverage..."
        python -m pytest tests/ --cov=app --cov-report=html --cov-report=term
        ;;
    "run")
        echo "Starting development server..."
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
        ;;
    "migrate")
        echo "Running migrations..."
        alembic upgrade head
        ;;
    "migrate-new")
        echo "Creating new migration..."
        alembic revision --autogenerate -m "${2:-auto migration}"
        ;;
    *)
        echo "Streaklet Development Helper"
        echo ""
        echo "Usage: ./dev.sh [command]"
        echo ""
        echo "Commands:"
        echo "  test         Run test suite"
        echo "  test-cov     Run tests with coverage report"
        echo "  run          Start development server"
        echo "  migrate      Run database migrations"
        echo "  migrate-new  Create new migration"
        ;;
esac
