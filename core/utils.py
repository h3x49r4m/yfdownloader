"""
Utility functions for the Yahoo Finance downloader
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional, Union
import json
import csv
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """
    Setup logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path
    """
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=handlers
    )


def validate_date_format(date_str: str) -> bool:
    """
    Validate date string format (YYYY-MM-DD)
    
    Args:
        date_str: Date string to validate
        
    Returns:
        True if valid format, False otherwise
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validate_date_range(start_date: str, end_date: str) -> bool:
    """
    Validate that start_date is before end_date
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        
    Returns:
        True if valid range, False otherwise
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        return start <= end
    except ValueError:
        return False


def get_default_date_range(days_back: int = 365) -> tuple:
    """
    Get default date range (last N days)
    
    Args:
        days_back: Number of days to go back
        
    Returns:
        Tuple of (start_date, end_date) in YYYY-MM-DD format
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    return (
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )


def parse_ticker_list(ticker_str: str) -> List[str]:
    """
    Parse ticker string into list
    
    Args:
        ticker_str: Comma-separated ticker string
        
    Returns:
        List of ticker symbols
    """
    if not ticker_str:
        return []
    
    tickers = [ticker.strip() for ticker in ticker_str.split(',') if ticker.strip()]
    return tickers


def load_config(config_file: str) -> Dict:
    """
    Load configuration from JSON file
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        logger.error(f"Error loading config from {config_file}: {str(e)}")
        return {}


def save_config(config: Dict, config_file: str):
    """
    Save configuration to JSON file
    
    Args:
        config: Configuration dictionary
        config_file: Path to save configuration
    """
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving config to {config_file}: {str(e)}")


def create_directory(directory: str) -> bool:
    """
    Create directory if it doesn't exist
    
    Args:
        directory: Directory path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        Path(directory).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {directory}: {str(e)}")
        return False


def get_file_size(filepath: str) -> int:
    """
    Get file size in bytes
    
    Args:
        filepath: Path to file
        
    Returns:
        File size in bytes
    """
    try:
        return os.path.getsize(filepath)
    except OSError:
        return 0


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def validate_ticker_format(ticker: str) -> bool:
    """
    Validate ticker format
    
    Args:
        ticker: Ticker symbol
        
    Returns:
        True if valid format, False otherwise
    """
    if not ticker or not isinstance(ticker, str):
        return False
    
    # Basic validation: alphanumeric, 1-10 characters
    ticker = ticker.strip().upper()
    return ticker.isalnum() and 1 <= len(ticker) <= 10


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """
    Split list into chunks
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def merge_csv_files(
    input_files: List[str],
    output_file: str,
    remove_duplicates: bool = True
) -> bool:
    """
    Merge multiple CSV files into one
    
    Args:
        input_files: List of input CSV files
        output_file: Output CSV file path
        remove_duplicates: Whether to remove duplicate rows
        
    Returns:
        True if successful, False otherwise
    """
    try:
        all_data = []
        
        for file in input_files:
            try:
                df = pd.read_csv(file)
                all_data.append(df)
            except Exception as e:
                logger.error(f"Error reading {file}: {str(e)}")
                continue
        
        if not all_data:
            logger.error("No valid data to merge")
            return False
        
        # Concatenate all data
        merged_df = pd.concat(all_data, ignore_index=True)
        
        # Remove duplicates if requested
        if remove_duplicates:
            merged_df = merged_df.drop_duplicates()
        
        # Save merged data
        merged_df.to_csv(output_file, index=False)
        
        logger.info(f"Merged {len(input_files)} files into {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"Error merging CSV files: {str(e)}")
        return False


def get_available_countries(data_dir: str = "data/tickers") -> List[str]:
    """
    Get list of available countries with ticker files
    
    Args:
        data_dir: Directory containing ticker files
        
    Returns:
        List of country codes
    """
    try:
        ticker_dir = Path(data_dir)
        if not ticker_dir.exists():
            return []
        
        countries = []
        # Look for country directories
        for country_dir in ticker_dir.iterdir():
            if country_dir.is_dir():
                countries.append(country_dir.name)
        
        return sorted(countries)
    except Exception as e:
        logger.error(f"Error getting available countries: {str(e)}")
        return []


def estimate_download_time(
    num_tickers: int,
    avg_time_per_ticker: float = 0.5,
    max_concurrent: int = 50
) -> float:
    """
    Estimate download time in seconds
    
    Args:
        num_tickers: Number of tickers to download
        avg_time_per_ticker: Average time per ticker in seconds
        max_concurrent: Maximum concurrent downloads
        
    Returns:
        Estimated time in seconds
    """
    if num_tickers <= max_concurrent:
        return avg_time_per_ticker
    else:
        batches = num_tickers / max_concurrent
        return batches * avg_time_per_ticker


def format_time(seconds: float) -> str:
    """
    Format time in human-readable format
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted time string
    """
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} hours"