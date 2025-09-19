# Makefile for Receipt Processor
# Provides convenient commands for development, testing, and deployment

.PHONY: help install install-dev test test-unit test-integration test-e2e test-performance test-all lint format type-check security clean build docs coverage pre-commit setup

# Default target
help: ## Show this help message
	@echo "Receipt Processor - Available Commands:"
	@echo "======================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation
install: ## Install the package
	pip install -e .

install-dev: ## Install development dependencies
	pip install -e ".[dev]"

install-test: ## Install test dependencies
	pip install -e ".[test]"

install-lint: ## Install linting dependencies
	pip install -e ".[lint]"

install-security: ## Install security dependencies
	pip install -e ".[security]"

# Setup
setup: install-dev pre-commit ## Complete development setup
	@echo "Development environment setup complete!"

pre-commit: ## Install pre-commit hooks
	pre-commit install
	pre-commit install --hook-type commit-msg

# Testing
test: ## Run all tests
	python -m pytest tests/ -v

test-unit: ## Run unit tests only
	python -m pytest tests/test_unit_*.py -v -m "unit"

test-integration: ## Run integration tests only
	python -m pytest tests/test_integration_*.py -v -m "integration"

test-e2e: ## Run end-to-end tests only
	python -m pytest tests/test_e2e_*.py -v -m "e2e"

test-performance: ## Run performance tests only
	python -m pytest tests/test_performance.py -v -m "performance"

test-slow: ## Run slow tests
	python -m pytest tests/ -v -m "slow"

test-fast: ## Run fast tests only
	python -m pytest tests/ -v -m "not slow"

test-coverage: ## Run tests with coverage report
	python -m pytest tests/ --cov=src/receipt_processor --cov-report=html --cov-report=term-missing

test-parallel: ## Run tests in parallel
	python -m pytest tests/ -n auto

test-specific: ## Run specific test (usage: make test-specific TEST=test_name)
	python -m pytest tests/ -k $(TEST) -v

test-all: test-unit test-integration test-e2e test-performance ## Run all test suites

# Code Quality
lint: ## Run all linting tools
	@echo "Running flake8..."
	python -m flake8 src/ tests/
	@echo "Running black check..."
	python -m black --check src/ tests/
	@echo "Running isort check..."
	python -m isort --check-only src/ tests/
	@echo "Running mypy..."
	python -m mypy src/

format: ## Format code with black and isort
	@echo "Running black..."
	python -m black src/ tests/
	@echo "Running isort..."
	python -m isort src/ tests/

type-check: ## Run type checking with mypy
	python -m mypy src/

# Security
security: ## Run security checks
	@echo "Running bandit..."
	python -m bandit -r src/ -f json -o bandit-report.json
	@echo "Running safety..."
	python -m safety check

# Pre-commit
pre-commit-run: ## Run pre-commit on all files
	pre-commit run --all-files

pre-commit-update: ## Update pre-commit hooks
	pre-commit autoupdate

# Coverage
coverage: ## Generate coverage report
	python -m coverage run -m pytest tests/
	python -m coverage report
	python -m coverage html
	@echo "Coverage report generated in htmlcov/"

coverage-xml: ## Generate XML coverage report
	python -m coverage run -m pytest tests/
	python -m coverage xml

# Documentation
docs: ## Generate documentation
	@echo "Documentation generation not yet implemented"

docs-serve: ## Serve documentation locally
	@echo "Documentation serving not yet implemented"

# Build and Distribution
build: ## Build the package
	python -m build

build-clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/

# Cleaning
clean: ## Clean all generated files
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .tox/
	rm -rf bandit-report.json
	rm -rf test-results.xml
	rm -rf coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

clean-logs: ## Clean log files
	rm -f *.log
	rm -f logs/*.log
	rm -f error_log.json
	rm -f receipt_processing_log.json
	rm -f payment_tracking_log.json

# Development
dev-install: install-dev pre-commit ## Install development environment
	@echo "Development environment ready!"

dev-test: test-unit test-integration ## Run development tests

dev-lint: lint format type-check ## Run development linting

dev-check: dev-lint dev-test security ## Run all development checks

# CI/CD
ci-test: ## Run tests for CI
	python -m pytest tests/ --cov=src/receipt_processor --cov-report=xml --junitxml=test-results.xml

ci-lint: ## Run linting for CI
	python -m flake8 src/ tests/
	python -m black --check src/ tests/
	python -m isort --check-only src/ tests/
	python -m mypy src/

ci-security: ## Run security checks for CI
	python -m bandit -r src/ -f json -o bandit-report.json
	python -m safety check --json --output safety-report.json

ci-all: ci-lint ci-test ci-security ## Run all CI checks

# Database
db-reset: ## Reset database (if applicable)
	@echo "Database reset not applicable for this project"

# Docker
docker-build: ## Build Docker image
	docker build -t receipt-processor .

docker-run: ## Run Docker container
	docker run -it receipt-processor

docker-test: ## Run tests in Docker
	docker run -it receipt-processor python -m pytest tests/

# Monitoring
monitor-start: ## Start system monitoring
	python -m src.receipt_processor.cli monitor --start-monitoring

monitor-stop: ## Stop system monitoring
	python -m src.receipt_processor.cli monitor --stop-monitoring

monitor-status: ## Check monitoring status
	python -m src.receipt_processor.cli monitor --status

# Health checks
health: ## Check system health
	python -m src.receipt_processor.cli health

metrics: ## Show system metrics
	python -m src.receipt_processor.cli metrics

alerts: ## Show system alerts
	python -m src.receipt_processor.cli alerts

# Error handling
error-log: ## Show error log
	python -m src.receipt_processor.cli error-log

# Performance
benchmark: ## Run performance benchmarks
	python -m pytest tests/test_performance.py -v -m "performance" --benchmark-only

load-test: ## Run load tests
	python -m pytest tests/test_performance.py -v -m "slow" -k "load"

# Utilities
check-deps: ## Check for outdated dependencies
	pip list --outdated

update-deps: ## Update dependencies
	pip install --upgrade pip
	pip install --upgrade -r requirements.txt

validate-config: ## Validate configuration
	python -m src.receipt_processor.cli config validate

# Release
release-check: ## Check if ready for release
	@echo "Checking release readiness..."
	@echo "Running tests..."
	make test-all
	@echo "Running linting..."
	make lint
	@echo "Running security checks..."
	make security
	@echo "Checking coverage..."
	make coverage
	@echo "Release check complete!"

release-prepare: ## Prepare for release
	@echo "Preparing release..."
	make clean
	make test-all
	make lint
	make security
	make build
	@echo "Release preparation complete!"

# Helpers
version: ## Show version information
	python -c "import src.receipt_processor; print(src.receipt_processor.__version__)"

info: ## Show project information
	@echo "Receipt Processor - AI-powered receipt processing system"
	@echo "Version: $(shell python -c "import src.receipt_processor; print(src.receipt_processor.__version__)")"
	@echo "Python: $(shell python --version)"
	@echo "Platform: $(shell uname -s)"

# Default target
.DEFAULT_GOAL := help
