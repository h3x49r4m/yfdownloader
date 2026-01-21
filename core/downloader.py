"""
Parallel Yahoo Finance data downloader
"""

import asyncio
import aiohttp
import yfinance as yf
import pandas as pd
from typing import List, Dict, Optional, Union
from datetime import datetime, timedelta
import logging
from pathlib import Path
import time
from tqdm.asyncio import tqdm

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ParallelDownloader:
    """High-performance parallel Yahoo Finance data downloader"""
    
    def __init__(
        self,
        max_concurrent: int = 50,
        retry_attempts: int = 3,
        retry_delay: float = 1.0,
        timeout: int = 30
    ):
        """
        Initialize the parallel downloader
        
        Args:
            max_concurrent: Maximum number of concurrent downloads
            retry_attempts: Number of retry attempts for failed downloads
            retry_delay: Delay between retries in seconds
            timeout: Request timeout in seconds
        """
        self.max_concurrent = max_concurrent
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
    async def download_ticker(
        self,
        ticker: str,
        start_date: str,
        end_date: str,
        session: aiohttp.ClientSession,
        period: Optional[str] = None,
        auto_adjust: bool = True
    ) -> Optional[pd.DataFrame]:
        """
        Download data for a single ticker with retry logic
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            session: aiohttp session
            period: Period parameter (e.g., "max", "1y", "5y") - if provided, ignores start/end dates
            
        Returns:
            DataFrame with OHLCV data or None if failed
        """
        # Extract ticker symbol for display
        ticker_parts = ticker.split(',')
        ticker_symbol = ticker_parts[0].strip()
        ticker_name = ticker_parts[1].strip() if len(ticker_parts) > 1 else ""
        
        async with self.semaphore:
            for attempt in range(self.retry_attempts):
                try:
                    # Use yfinance to download data
                    stock = yf.Ticker(ticker_symbol)
                    
                    # Use period if provided, otherwise use start/end dates
                    if period:
                        data = stock.history(
                            period=period,
                            auto_adjust=auto_adjust,
                            prepost=False
                        )
                    else:
                        data = stock.history(
                            start=start_date,
                            end=end_date,
                            auto_adjust=auto_adjust,
                            prepost=False
                        )
                    
                    if data.empty:
                        logger.warning(f"No data found for ticker: {ticker_symbol} ({ticker_name})")
                        return None
                    
                    # Add ticker column - use only the ticker symbol
                    data['ticker'] = ticker_parts[0].strip()
                    data.reset_index(inplace=True)
                    
                    # Rename columns to standard format
                    data.rename(columns={
                        'Date': 'date',
                        'Open': 'open',
                        'High': 'high',
                        'Low': 'low',
                        'Close': 'close',
                        'Volume': 'volume',
                        'Dividends': 'dividends',
                        'Stock Splits': 'stock_splits'
                    }, inplace=True)
                    
                    # Format numeric columns for better readability
                    numeric_columns = ['open', 'high', 'low', 'close']
                    for col in numeric_columns:
                        if col in data.columns:
                            data[col] = data[col].round(4)
                    
                    # Format date column to remove time component if present
                    if 'date' in data.columns:
                        data['date'] = pd.to_datetime(data['date']).dt.strftime('%Y-%m-%d')
                    
                    return data
                    
                except Exception as e:
                    display_name = f"{ticker_symbol} ({ticker_name})" if ticker_name else ticker_symbol
                    logger.warning(f"Attempt {attempt + 1} failed for {display_name}: {str(e)}")
                    if attempt < self.retry_attempts - 1:
                        await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    else:
                        logger.error(f"Failed to download data for {display_name} after {self.retry_attempts} attempts")
                        return None
    
    async def download_tickers(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        output_dir: str = "data/downloads",
        output_format: str = "csv",
        period: Optional[str] = None,
        auto_adjust: bool = True
    ) -> Dict[str, Union[int, List[str]]]:
        """
        Download data for multiple tickers in parallel
        
        Args:
            tickers: List of ticker symbols
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            output_dir: Directory to save downloaded data
            output_format: Output format (csv, parquet, json)
            
        Returns:
            Dictionary with download statistics
        """
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Create aiohttp session
        connector = aiohttp.TCPConnector(limit=self.max_concurrent)
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Create progress bar
            pbar = tqdm(total=len(tickers), desc="Downloading tickers")
            
            # Create tasks for all tickers
            tasks = []
            for ticker in tickers:
                task = self.download_ticker(ticker, start_date, end_date, session, period, auto_adjust)
                # Extract ticker symbol for filename
                ticker_symbol = ticker.split(',')[0].strip() if ',' in ticker else ticker
                tasks.append((ticker, task, ticker_symbol))
            
            # Execute tasks and save results
            successful = []
            failed = []
            
            for ticker, task, ticker_symbol in tasks:
                try:
                    data = await task
                    if data is not None and not data.empty:
                        # Save data based on format
                        adjustment_suffix = "adj" if auto_adjust else "raw"
                        if period:
                            filename = f"{ticker_symbol}_{period}_{adjustment_suffix}.{output_format}"
                        else:
                            filename = f"{ticker_symbol}_{start_date}_{end_date}_{adjustment_suffix}.{output_format}"
                        filepath = Path(output_dir) / filename
                        
                        if output_format == "csv":
                            data.to_csv(filepath, index=False)
                        elif output_format == "parquet":
                            data.to_parquet(filepath, index=False)
                        elif output_format == "json":
                            data.to_json(filepath, orient='records', date_format='iso')
                        
                        successful.append(ticker)
                    else:
                        failed.append(ticker)
                except Exception as e:
                    logger.error(f"Error processing {ticker}: {str(e)}")
                    failed.append(ticker)
                finally:
                    pbar.update(1)
            
            pbar.close()
        
        return {
            "total": len(tickers),
            "successful": len(successful),
            "failed": len(failed),
            "successful_tickers": successful,
            "failed_tickers": failed
        }
    
    def download_sync(
        self,
        tickers: List[str],
        start_date: str,
        end_date: str,
        output_dir: str = "data/downloads",
        output_format: str = "csv",
        period: Optional[str] = None,
        auto_adjust: bool = True
    ) -> Dict[str, Union[int, List[str]]]:
        """
        Synchronous wrapper for async download
        
        Args:
            tickers: List of ticker symbols
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            output_dir: Directory to save downloaded data
            output_format: Output format (csv, parquet, json)
            period: Period parameter (e.g., "max", "1y", "5y") - if provided, ignores start/end dates
            
        Returns:
            Dictionary with download statistics
        """
        return asyncio.run(
            self.download_tickers(
                tickers=tickers,
                start_date=start_date,
                end_date=end_date,
                output_dir=output_dir,
                output_format=output_format,
                period=period,
                auto_adjust=auto_adjust
            )
        )
    
    def get_ticker_info(self, ticker: str) -> Optional[Dict]:
        """
        Get detailed information about a ticker
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with ticker information
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return info
        except Exception as e:
            logger.error(f"Error getting info for {ticker}: {str(e)}")
            return None


def load_tickers_from_file(filepath: str) -> List[str]:
    """
    Load tickers from a text file
    
    Args:
        filepath: Path to ticker file
        
    Returns:
        List of ticker symbols
    """
    try:
        with open(filepath, 'r') as f:
            tickers = []
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):  # Skip empty lines and comments
                    # Handle ticker,name format - extract only the ticker part
                    if ',' in line:
                        ticker = line.split(',')[0].strip()
                    else:
                        ticker = line
                    tickers.append(ticker)
        return tickers
    except Exception as e:
        logger.error(f"Error loading tickers from {filepath}: {str(e)}")
        return []


def get_country_tickers(country: str, data_dir: str = "data/tickers") -> List[str]:
    """
    Get tickers for a specific country
    
    Args:
        country: Country code (us, uk, jp, de, cn)
        data_dir: Directory containing ticker files
        
    Returns:
        List of ticker symbols
    """
    country_dir = Path(data_dir) / country.lower()
    
    # For China, return all tickers from all sub-files
    if country.lower() == 'cn':
        all_tickers = []
        for file_path in country_dir.glob("*.txt"):
            if file_path.name != 'cn.txt':  # Skip the index file
                tickers = load_tickers_from_file(str(file_path))
                all_tickers.extend(tickers)
        return all_tickers
    
    # For other countries, look for the main ticker file
    ticker_file = country_dir / f"{country.lower()}.txt"
    if ticker_file.exists():
        return load_tickers_from_file(str(ticker_file))
    
    return []