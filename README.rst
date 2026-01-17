Yahoo Finance Parallel Downloader
====================================

A high-performance parallel downloader for fetching OHLCV (Open, High, Low, Close, Volume) data from Yahoo Finance for multiple tickers simultaneously.

Features
--------

* **Parallel Processing**: Download data for hundreds of tickers simultaneously
* **Multiple Markets**: Support for US, UK, Japan, Germany, and China markets
* **Flexible Input**: Specify tickers via CLI arguments, files, or by country
* **Multiple Output Formats**: CSV, Parquet, and JSON support
* **Data Processing**: Built-in validation, technical indicators, and returns calculation
* **Resume Capability**: Resume interrupted downloads
* **Progress Tracking**: Real-time progress bars and detailed logging
* **Error Handling**: Robust retry mechanism with exponential backoff
* **UV-Powered**: Fast dependency management with UV

Installation
------------

Prerequisites
~~~~~~~~~~~~~~

* Python 3.10 or higher
* `UV <https://docs.astral.sh/uv/>`_ package manager

Quick Setup
~~~~~~~~~~~

.. code-block:: bash

    # Clone the repository
    git clone https://github.com/h3x49r4m/yfdownloader.git
    cd yfdownloader

    # Install dependencies with UV
    uv sync

    # Or install development dependencies
    uv sync --dev


Quick Start
-----------

.. code-block:: bash

    # Download specific tickers
    uv run yfdownloader download --tickers "AAPL,GOOGL,MSFT" --start-date 2020-01-01 --end-date 2023-12-31

    # Download all US tickers
    uv run yfdownloader download --country us --start-date 2020-01-01 --end-date 2023-12-31

    # Download multiple countries with custom concurrency
    uv run yfdownloader download --countries us,uk,jp --start-date 2020-01-01 --end-date 2023-12-31 --concurrency 100

    # Download from custom ticker file
    uv run yfdownloader download --file data/tickers/us/us.txt --start-date 2020-01-01 --end-date 2023-12-31

CLI Commands
------------

Download Command
~~~~~~~~~~~~~~~~

.. code-block:: bash

    uv run yfdownloader download [OPTIONS]

**Options:**

* ``--tickers``: Comma-separated list of ticker symbols
* ``--file``: File containing ticker symbols (one per line)
* ``--country``: Country code (us, uk, jp, de, cn)
* ``--countries``: Comma-separated list of country codes
* ``--start-date``: Start date in YYYY-MM-DD format
* ``--end-date``: End date in YYYY-MM-DD format
* ``--days``: Number of days to look back (default: 365)
* ``--output-dir``: Output directory (default: data/downloads)
* ``--format``: Output format (csv, parquet, json)
* ``--concurrency``: Maximum concurrent downloads (default: 50)
* ``--retry``: Retry attempts (default: 3)
* ``--timeout``: Request timeout in seconds (default: 30)
* ``--add-indicators``: Add technical indicators
* ``--validate``: Validate and clean data

List Tickers
~~~~~~~~~~~~

.. code-block:: bash

    # List all available countries
    uv run yfdownloader list-tickers

    # List tickers for a specific country
    uv run yfdownloader list-tickers --country us

Get Ticker Information
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    uv run yfdownloader info AAPL --start-date 2023-01-01 --end-date 2023-12-31

Data Processing Commands
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Merge all data files in a directory
    uv run yfdownloader data merge data/downloads merged_data.csv

    # Process data with indicators and validation
    uv run yfdownloader data process data.csv --add-indicators --validate --returns

    # Show summary statistics
    uv run yfdownloader data summary data.csv

    # Filter data by date range
    uv run yfdownloader data filter data.csv --start-date 2023-01-01 --end-date 2023-06-30

Using Make Commands
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Install dependencies
    make install

    # Run example download
    make run-example

    # Download US stocks
    make download-us

    # Download all countries
    make download-all

    # Run tests
    make test

Architecture
------------

The project is organized into three main components:

Core Module (``core/``)
~~~~~~~~~~~~~~~~~~~~~~

* ``downloader.py``: AsyncIO-based parallel downloads
* ``processor.py``: Data processing and validation utilities
* ``utils.py``: Common utility functions

CLI Module (``cli/``)
~~~~~~~~~~~~~~~~~~~~

* ``main.py``: Main CLI interface and commands
* ``commands.py``: Additional data processing commands

Data Module (``data/``)
~~~~~~~~~~~~~~~~~~~~~~

* ``tickers/``: Ticker files organized by country

  * ``us/``: US stock tickers
  * ``uk/``: UK stock tickers
  * ``jp/``: Japan stock tickers
  * ``de/``: Germany stock tickers
  * ``cn/``: Chinese stock tickers (ADRs, HK, Shanghai, Shenzhen)

* ``downloads/``: Default output directory for downloaded data

Configuration Files
~~~~~~~~~~~~~~~~~~~

* ``pyproject.toml``: Project configuration and dependencies (UV-based)
* ``uv.lock``: Locked dependencies for reproducibility
* ``.python-version``: Python version specification
* ``Makefile``: Build and development commands

Comprehensive Usage
-------------------

Download Commands
~~~~~~~~~~~~~~~~~

**Basic Ticker Downloads**

.. code-block:: bash

    # Download single ticker
    uv run yfdownloader download --tickers "AAPL" --days 365

    # Download multiple tickers
    uv run yfdownloader download --tickers "AAPL,GOOGL,MSFT,AMZN,META" --days 365

    # Download with specific date range
    uv run yfdownloader download --tickers "AAPL" --start-date 2020-01-01 --end-date 2023-12-31

    # Download all available history
    uv run yfdownloader download --tickers "AAPL" --start-date 1970-01-01

**Country-Based Downloads**

.. code-block:: bash

    # Download all US stocks
    uv run yfdownloader download --country us --days 365

    # Download all Chinese stocks
    uv run yfdownloader download --country cn --days 365

    # Download multiple countries
    uv run yfdownloader download --countries us,uk,jp,de,cn --days 365

    # Download specific Chinese markets
    uv run yfdownloader download --file data/tickers/cn/cn_adrs.txt --days 365
    uv run yfdownloader download --file data/tickers/cn/cn_hk.txt --days 365
    uv run yfdownloader download --file data/tickers/cn/cn_shanghai.txt --days 365
    uv run yfdownloader download --file data/tickers/cn/cn_shenzhen.txt --days 365

**File-Based Downloads**

.. code-block:: bash

    # Download from ticker file
    uv run yfdownloader download --file data/tickers/us/us.txt --days 365

    # Download from custom ticker file
    uv run yfdownloader download --file my_tickers.txt --days 365

    # Download from multiple files
    uv run yfdownloader download --file data/tickers/us/us.txt --file data/tickers/uk/uk.txt --days 365

**Output Format Options**

.. code-block:: bash

    # CSV format (default)
    uv run yfdownloader download --tickers "AAPL" --days 365 --format csv

    # Parquet format (more efficient)
    uv run yfdownloader download --tickers "AAPL" --days 365 --format parquet

    # JSON format
    uv run yfdownloader download --tickers "AAPL" --days 365 --format json

**Output Directory Control**

.. code-block:: bash

    # Download to specific directory
    uv run yfdownloader download --tickers "AAPL" --days 365 --output-dir my_data

    # Download to absolute path
    uv run yfdownloader download --tickers "AAPL" --days 365 --output-dir /Users/username/financial_data

    # Download to nested directory
    uv run yfdownloader download --tickers "AAPL" --days 365 --output-dir data/2024/january/us_stocks

**Performance Tuning**

.. code-block:: bash

    # High concurrency for faster downloads
    uv run yfdownloader download --country us --days 365 --concurrency 100

    # Custom retry settings
    uv run yfdownloader download --country us --days 365 --retry 5 --timeout 60

    # Lower concurrency for rate-limited sources
    uv run yfdownloader download --country cn --days 365 --concurrency 20

**Data Processing Options**

.. code-block:: bash

    # Add technical indicators
    uv run yfdownloader download --tickers "AAPL" --days 365 --add-indicators

    # Validate and clean data
    uv run yfdownloader download --tickers "AAPL" --days 365 --validate

    # Both indicators and validation
    uv run yfdownloader download --tickers "AAPL" --days 365 --add-indicators --validate

    # Calculate returns
    uv run yfdownloader download --tickers "AAPL" --days 365 --add-indicators --returns

**Advanced Combinations**

.. code-block:: bash

    # Complete download with all options
    uv run yfdownloader download \
      --country us \
      --start-date 2020-01-01 \
      --end-date 2023-12-31 \
      --format parquet \
      --concurrency 100 \
      --add-indicators \
      --validate \
      --output-dir /Users/username/financial_data/us_complete

    # Download all markets with technical indicators
    uv run yfdownloader download \
      --countries us,uk,jp,de,cn \
      --days 365 \
      --format parquet \
      --concurrency 50 \
      --add-indicators \
      --output-dir global_markets

**Data Processing Commands**

.. code-block:: bash

    # List available countries and tickers
    uv run yfdownloader list-tickers
    uv run yfdownloader list-tickers --country us

    # Get ticker information
    uv run yfdownloader info AAPL --start-date 2023-01-01 --end-date 2023-12-31

    # Merge all downloaded files
    uv run yfdownloader data merge data/downloads all_data.csv

    # Process existing data
    uv run yfdownloader data process data.csv --add-indicators --validate --returns

    # Get summary statistics
    uv run yfdownloader data summary data.csv

    # Filter data by date range
    uv run yfdownloader data filter data.csv \
      --start-date 2023-01-01 \
      --end-date 2023-06-30 \
      --output 2023_h1.csv

**Make Command Usage**

.. code-block:: bash

    # Quick setup and installation
    make install
    make install-dev

    # Example downloads
    make run-example
    make download-us
    make download-all

    # Data processing
    make process-data

    # Development
    make test
    make format
    make lint

    # Documentation
    make docs
    make build-docs
    make serve-docs

**Real-World Scenarios**

.. code-block:: bash

    # Quantitative research setup
    uv run yfdownloader download \
      --countries us,uk,jp \
      --start-date 2015-01-01 \
      --days 3650 \
      --format parquet \
      --add-indicators \
      --validate \
      --concurrency 50 \
      --output-dir research_data

    # Day trading data preparation
    uv run yfdownloader download \
      --tickers "AAPL,GOOGL,MSFT,TSLA,NVDA" \
      --days 30 \
      --format csv \
      --concurrency 10 \
      --output-dir day_trading

    # Portfolio analysis
    uv run yfdownloader download \
      --tickers "SPY,QQQ,IWM,EFA,EEM,GLD,TLT" \
      --start-date 2010-01-01 \
      --days 5000 \
      --format parquet \
      --add-indicators \
      --output-dir portfolio_analysis

    # International market comparison
    uv run yfdownloader download \
      --countries us,uk,de,jp,cn \
      --start-date 2020-01-01 \
      --days 1500 \
      --format parquet \
      --concurrency 30 \
      --output-dir international_comparison

**Error Handling and Troubleshooting**

.. code-block:: bash

    # Download with increased retry for unreliable connections
    uv run yfdownloader download --country us --days 365 --retry 10 --timeout 120

    # Download with verbose logging
    uv run yfdownloader download --country us --days 365 --log-level DEBUG

    # Download with custom log file
    uv run yfdownloader download --country us --days 365 --log-file download.log

Example Usage
-------------

Basic Download
~~~~~~~~~~~~~~

.. code-block:: bash

    # Download last year of data for FAANG stocks
    uv run yfdownloader download --tickers "META,AAPL,AMZN,NFLX,GOOGL" --days 365

Advanced Download with Processing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Download S&P 500 stocks with technical indicators
    uv run yfdownloader download \
      --country us \
      --start-date 2020-01-01 \
      --end-date 2023-12-31 \
      --concurrency 100 \
      --add-indicators \
      --validate \
      --format parquet

Chinese Market Downloads
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Download all Chinese stocks
    uv run yfdownloader download --country cn --days 365 --format parquet

    # Download specific Chinese markets
    uv run yfdownloader download --file data/tickers/cn/cn_adrs.txt --days 365
    uv run yfdownloader download --file data/tickers/cn/cn_hk.txt --days 365
    uv run yfdownloader download --file data/tickers/cn/cn_shanghai.txt --days 365
    uv run yfdownloader download --file data/tickers/cn/cn_shenzhen.txt --days 365

    # Download Chinese stocks with technical indicators
    uv run yfdownloader download --country cn --days 365 --add-indicators --format parquet

Data Analysis
~~~~~~~~~~~~~

.. code-block:: bash

    # Merge all downloaded data
    uv run yfdownloader data merge data/downloads all_stocks.csv

    # Get summary statistics
    uv run yfdownloader data summary all_stocks.csv

    # Filter for specific date range
    uv run yfdownloader data filter all_stocks.csv \
      --start-date 2023-01-01 \
      --end-date 2023-06-30 \
      --output 2023_h1.csv

    # Process data with indicators and returns
    uv run yfdownloader data process all_stocks.csv --add-indicators --validate --returns

Custom Output Directory
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Download to specific directory
    uv run yfdownloader download --tickers "AAPL" --days 365 --output-dir my_data

    # Download with absolute path
    uv run yfdownloader download --country us --days 365 --output-dir /Users/username/financial_data

    # Download to nested directory structure
    uv run yfdownloader download --country us --days 365 --output-dir data/2024/us_stocks

Advanced Examples
~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Download with all features enabled
    uv run yfdownloader download \
      --tickers "AAPL,GOOGL,MSFT" \
      --start-date 2020-01-01 \
      --end-date 2023-12-31 \
      --format parquet \
      --concurrency 50 \
      --add-indicators \
      --validate \
      --output-dir advanced_example

    # Download all available history for major indices
    uv run yfdownloader download \
      --tickers "SPY,QQQ,IWM,DIA,VTI" \
      --start-date 2000-01-01 \
      --format parquet \
      --add-indicators \
      --output-dir indices_history

    # Download with error handling and logging
    uv run yfdownloader download \
      --country us \
      --days 365 \
      --concurrency 100 \
      --retry 5 \
      --timeout 60 \
      --log-level INFO \
      --log-file download.log \
      --output-dir robust_download

    # Download specific sectors
    uv run yfdownloader download \
      --tickers "XLF,XLE,XLU,XLI,XLV,XLY,XLP,XLB,XLC,XLK" \
      --days 365 \
      --format parquet \
      --add-indicators \
      --output-dir sector_etfs

    # Download for backtesting
    uv run yfdownloader download \
      --tickers "AAPL,MSFT,GOOGL,AMZN,META,TSLA,NVDA" \
      --start-date 2015-01-01 \
      --days 3000 \
      --format parquet \
      --add-indicators \
      --validate \
      --output-dir backtesting_data

Development
-----------

Setting Up Development Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Clone the repository
    git clone https://github.com/yourusername/yfdownloader.git
    cd yfdownloader

    # Install development dependencies
    uv sync --dev

    # Run tests
    uv run pytest

    # Format code
    uv run black .

    # Lint code
    uv run flake8 core/ cli/

    # Type checking
    uv run mypy core/ cli/

Using Make Commands
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Development commands
    make install-dev  # Install dev dependencies
    make test        # Run tests
    make format      # Format code
    make lint        # Run linting
    make clean       # Clean build artifacts

Adding New Dependencies
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Add runtime dependency
    uv add requests

    # Add development dependency
    uv add --dev pytest

    # Update lock file
    uv lock

Contributing
------------

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

License
-------

This project is licensed under the Apache 2.0 License - see the LICENSE file for details.

Disclaimer
----------

This software is for educational and research purposes only. The data is provided "as is" without any warranties. Always verify data accuracy before making financial decisions.
