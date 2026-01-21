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
	@echo "  download-cn  Download Chinese market tickers"
	@echo "  download-all Download all countries"
	@echo "  process-data Process downloaded data"
	@echo "  split-large  Split large ticker files for optimization"
	@echo ""
	@echo "Advanced download commands:"
	@echo "  download-raw Download unadjusted prices"
	@echo "  download-max Download maximum history"
	@echo "  download-log Download with detailed logging"
	@echo ""
	@echo "Performance commands:"
	@echo "  benchmark    Test download performance"
	@echo "  stress-test  Stress test with many tickers"
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

# Clean downloaded data
clean-data:
	rm -rf data/downloads/
	rm -rf ./data/*.csv
	rm -rf ./data/*.parquet
	rm -rf ./data/*.json
	rm -f *.log

# Clean all generated files
clean-all: clean clean-data
	@echo "All build artifacts and data cleaned"

# Check disk usage of downloaded data
disk-usage:
	@echo "Disk usage of downloaded data:"
	@du -sh data/downloads/ 2>/dev/null || echo "No data/downloads directory"
	@du -sh ./data/*.csv 2>/dev/null || echo "No CSV files in current directory"
	@du -sh ./data/*.parquet 2>/dev/null || echo "No Parquet files in current directory"

# Show statistics of downloaded files
stats:
	@echo "Download statistics:"
	@if [ -d "data/downloads" ]; then \
		echo "Files in data/downloads: $$(ls data/downloads/ | wc -l)"; \
		echo "Total size: $$(du -sh data/downloads/ | cut -f1)"; \
	else \
		echo "No data/downloads directory"; \
	fi

# Run example download
run-example:
	uv run yfdownloader download --tickers "AAPL,GOOGL,MSFT" --period 1y --concurrency 10

# Quick demo with all features
demo:
	uv run yfdownloader download --tickers "AAPL,GOOGL" --period 1y --add-indicators --validate --output-dir ./demo

# Test ticker,name format
test-format:
	uv run yfdownloader download --tickers "AAPL,Apple Inc." --period 1y --output-dir ./test_format

# Show available tickers
list-tickers:
	uv run yfdownloader list-tickers
	uv run yfdownloader list-tickers --country us

# Download all US tickers
download-us:
	uv run yfdownloader download --file data/tickers/us/us.txt --days 365 --concurrency 50 --format parquet

# Download Chinese market tickers (optimized)
download-cn:
	uv run yfdownloader download --file data/tickers/cn/cn_shanghai.txt --period 1y --concurrency 20 --output-dir ./data/shanghai
	uv run yfdownloader download --file data/tickers/cn/cn_shenzhen.txt --period 1y --concurrency 20 --output-dir ./data/shenzhen
	uv run yfdownloader download --file data/tickers/cn/cn_adrs.txt --period max --concurrency 50 --output-dir ./data/adrs

# Download all countries
download-all:
	uv run yfdownloader download --countries us,uk,jp,de,cn --days 365 --concurrency 100 --format parquet

# Download unadjusted prices (for dividend analysis)
download-raw:
	uv run yfdownloader download --file data/tickers/us/us.txt --period 5y --no-adjust --output-dir ./data/raw_prices

# Download maximum history
download-max:
	uv run yfdownloader download --tickers "AAPL,GOOGL,MSFT,AMZN,TSLA,META" --period max --output-dir ./data/max_history

# Download with detailed logging
download-log:
	uv run yfdownloader download --file data/tickers/us/us.txt --period 1y --log-level DEBUG --log-file download.log --output-dir ./data/with_logs

# Process downloaded data
process-data:
	uv run yfdownloader data merge data/downloads all_data.parquet --format parquet
	uv run yfdownloader data process all_data.parquet --add-indicators --validate --returns

# Split large ticker files for optimization
split-large:
	@echo "Splitting large ticker files..."
	head -n 500 data/tickers/cn/cn_shenzhen.txt > data/tickers/cn/cn_shenzhen_part1.txt
	tail -n +501 data/tickers/cn/cn_shenzhen.txt | head -n 500 > data/tickers/cn/cn_shenzhen_part2.txt
	tail -n +1001 data/tickers/cn/cn_shenzhen.txt > data/tickers/cn/cn_shenzhen_part3.txt
	@echo "Split into 3 files for parallel downloading"

# Parallel download example (run in background)
download-parallel:
	@echo "Starting parallel downloads..."
	uv run yfdownloader download --file data/tickers/cn/cn_shenzhen_part1.txt --period max --concurrency 30 --output-dir ./data/part1 &
	uv run yfdownloader download --file data/tickers/cn/cn_shenzhen_part2.txt --period max --concurrency 30 --output-dir ./data/part2 &
	uv run yfdownloader download --file data/tickers/cn/cn_shenzhen_part3.txt --period max --concurrency 30 --output-dir ./data/part3 &
	wait
	@echo "All parallel downloads completed!"

# Performance benchmark
benchmark:
	@echo "Running performance benchmark..."
	time uv run yfdownloader download --tickers "AAPL,MSFT,GOOGL,AMZN,TSLA" --period 1y --concurrency 50

# Stress test with many tickers
stress-test:
	@echo "Running stress test with 100 tickers..."
	time uv run yfdownloader download --file data/tickers/us/us.txt --period 30d --concurrency 100 --log-level INFO --log-file stress_test.log

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