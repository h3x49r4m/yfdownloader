# Makefile for yfdownloader - UV Version

.PHONY: help install install-dev test lint format clean run-example lock sync docs

# Default target
help:
	@echo "Yahoo Finance Parallel Downloader - UV Version"
	@echo ""
	@echo "Available commands:"
	@echo "  install      Install the package with uv"
	@echo "  install-dev  Install development dependencies with uv"
	@echo "  lock         Generate/uv lock file"
	@echo "  sync         Sync dependencies with uv"
	@echo "  test         Run tests"
	@echo "  lint         Run linting"
	@echo "  format       Format code"
	@echo "  clean        Clean build artifacts"
	@echo "  run-example  Run example download"
	@echo "  cli          Run CLI with uv"
	@echo "  docs         View documentation"
	@echo ""
	@echo "Data download commands:"
	@echo "  download-us  Download all US tickers"
	@echo "  download-all Download all countries"
	@echo "  process-data Process downloaded data"
	@echo ""
	@echo "Documentation commands:"
	@echo "  build-docs   Build HTML documentation"
	@echo "  serve-docs   Serve documentation locally"

# Install with uv
install:
	uv sync

# Install development dependencies
install-dev:
	uv sync --dev

# Generate lock file
lock:
	uv lock

# Sync dependencies
sync:
	uv sync

# Run tests
test:
	uv run pytest

# Run linting
lint:
	uv run flake8 core/ cli/
	uv run mypy core/ cli/

# Format code
format:
	uv run black core/ cli/
	uv run isort core/ cli/

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Run example download
run-example:
	uv run yfdownloader download --tickers "AAPL,GOOGL,MSFT" --days 30 --concurrency 10

# Download all US tickers
download-us:
	uv run yfdownloader download --file data/tickers/us/us.txt --days 365 --concurrency 50 --format parquet

# Download all countries
download-all:
	uv run yfdownloader download --countries us,uk,jp,de,cn --days 365 --concurrency 100 --format parquet

# Process downloaded data
process-data:
	uv run yfdownloader data merge data/downloads all_data.parquet --format parquet
	uv run yfdownloader data process all_data.parquet --add-indicators --validate --returns

# Run CLI
cli:
	uv run yfdownloader --help

# Development server (if applicable)
dev:
	uv run python -m cli.main --help

# Check dependencies
check:
	uv tree

# Update dependencies
update:
	uv sync --upgrade

# View documentation
docs:
	@echo "Opening README.rst..."
	@if command -v less >/dev/null 2>&1; then less README.rst; elif command -v more >/dev/null 2>&1; then more README.rst; else cat README.rst; fi

# Build documentation (if sphinx is available)
build-docs:
	@if command -v sphinx-build >/dev/null 2>&1; then \
		echo "Building documentation..."; \
		sphinx-build -b html docs/ docs/_build/html/; \
		echo "Documentation built in docs/_build/html/"; \
	else \
		echo "Sphinx not installed. Install with: uv add --dev sphinx"; \
	fi

# Serve documentation (if sphinx is available)
serve-docs:
	@if command -v sphinx-autobuild >/dev/null 2>&1; then \
		echo "Serving documentation at http://localhost:8000"; \
		sphinx-autobuild docs/ docs/_build/html/ --host 0.0.0.0 --port 8000; \
	else \
		echo "Sphinx-autobuild not installed. Install with: uv add --dev sphinx-autobuild"; \
	fi