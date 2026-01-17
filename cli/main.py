"""
Main CLI entry point for Yahoo Finance downloader
"""

import click
import sys
from pathlib import Path
import logging
from typing import List, Optional

# Add the parent directory to the path to import core modules
sys.path.append(str(Path(__file__).parent.parent))

from core.downloader import ParallelDownloader, load_tickers_from_file, get_country_tickers
from core.processor import DataProcessor
from core.utils import (
    setup_logging,
    validate_date_format,
    validate_date_range,
    get_default_date_range,
    parse_ticker_list,
    create_directory,
    get_available_countries,
    estimate_download_time,
    format_time
)

logger = logging.getLogger(__name__)


@click.group()
@click.option('--log-level', default='INFO', help='Logging level (DEBUG, INFO, WARNING, ERROR)')
@click.option('--log-file', help='Log file path')
@click.pass_context
def cli(ctx, log_level, log_file):
    """Yahoo Finance Parallel Data Downloader"""
    setup_logging(log_level, log_file)
    ctx.ensure_object(dict)
    ctx.obj['log_level'] = log_level
    ctx.obj['log_file'] = log_file


@cli.command()
@click.option('--tickers', help='Comma-separated list of ticker symbols')
@click.option('--file', 'ticker_file', help='File containing ticker symbols (one per line)')
@click.option('--country', help='Country code (us, uk, jp, de, cn)')
@click.option('--countries', help='Comma-separated list of country codes')
@click.option('--start-date', help='Start date in YYYY-MM-DD format')
@click.option('--end-date', help='End date in YYYY-MM-DD format')
@click.option('--days', default=365, help='Number of days to look back (default: 365)')
@click.option('--output-dir', default='data/downloads', help='Output directory (default: data/downloads)')
@click.option('--format', 'output_format', default='csv', type=click.Choice(['csv', 'parquet', 'json']), help='Output format')
@click.option('--concurrency', default=50, help='Maximum concurrent downloads (default: 50)')
@click.option('--retry', default=3, help='Retry attempts (default: 3)')
@click.option('--timeout', default=30, help='Request timeout in seconds (default: 30)')
@click.option('--add-indicators', is_flag=True, help='Add technical indicators')
@click.option('--validate', is_flag=True, help='Validate and clean data')
@click.pass_context
def download(ctx, tickers, ticker_file, country, countries, start_date, end_date, days, 
             output_dir, output_format, concurrency, retry, timeout, add_indicators, validate):
    """Download OHLCV data for specified tickers"""
    
    # Validate and parse tickers
    ticker_list = []
    
    if tickers:
        ticker_list.extend(parse_ticker_list(tickers))
    
    if ticker_file:
        file_tickers = load_tickers_from_file(ticker_file)
        if file_tickers:
            ticker_list.extend(file_tickers)
        else:
            click.echo(f"Warning: No tickers found in file {ticker_file}")
    
    if country:
        country_tickers = get_country_tickers(country)
        if country_tickers:
            ticker_list.extend(country_tickers)
        else:
            click.echo(f"Warning: No tickers found for country {country}")
    
    if countries:
        for c in parse_ticker_list(countries):
            country_tickers = get_country_tickers(c)
            if country_tickers:
                ticker_list.extend(country_tickers)
            else:
                click.echo(f"Warning: No tickers found for country {c}")
    
    if not ticker_list:
        click.echo("Error: No tickers specified. Use --tickers, --file, --country, or --countries")
        sys.exit(1)
    
    # Remove duplicates
    ticker_list = list(set(ticker_list))
    click.echo(f"Downloading data for {len(ticker_list)} tickers")
    
    # Validate and set date range
    if start_date and not validate_date_format(start_date):
        click.echo(f"Error: Invalid start date format: {start_date}. Use YYYY-MM-DD")
        sys.exit(1)
    
    if end_date and not validate_date_format(end_date):
        click.echo(f"Error: Invalid end date format: {end_date}. Use YYYY-MM-DD")
        sys.exit(1)
    
    if start_date and end_date and not validate_date_range(start_date, end_date):
        click.echo(f"Error: Invalid date range. Start date must be before end date.")
        sys.exit(1)
    
    if not start_date or not end_date:
        default_start, default_end = get_default_date_range(days)
        start_date = start_date or default_start
        end_date = end_date or default_end
    
    click.echo(f"Date range: {start_date} to {end_date}")
    
    # Create output directory
    if not create_directory(output_dir):
        click.echo(f"Error: Could not create output directory {output_dir}")
        sys.exit(1)
    
    # Estimate download time
    estimated_time = estimate_download_time(len(ticker_list), max_concurrent=concurrency)
    click.echo(f"Estimated download time: {format_time(estimated_time)}")
    
    # Initialize downloader
    downloader = ParallelDownloader(
        max_concurrent=concurrency,
        retry_attempts=retry,
        timeout=timeout
    )
    
    # Download data
    click.echo("Starting download...")
    results = downloader.download_sync(
        tickers=ticker_list,
        start_date=start_date,
        end_date=end_date,
        output_dir=output_dir,
        output_format=output_format
    )
    
    # Process data if requested
    if add_indicators or validate:
        click.echo("Processing downloaded data...")
        processor = DataProcessor()
        
        for ticker in results['successful_tickers']:
            try:
                filename = f"{ticker}_{start_date}_{end_date}.{output_format}"
                filepath = Path(output_dir) / filename
                
                if output_format == 'csv':
                    df = pd.read_csv(filepath)
                elif output_format == 'parquet':
                    df = pd.read_parquet(filepath)
                elif output_format == 'json':
                    df = pd.read_json(filepath)
                
                if validate:
                    df = processor.validate_data(df)
                
                if add_indicators:
                    df = processor.add_technical_indicators(df)
                
                # Save processed data
                if output_format == 'csv':
                    df.to_csv(filepath, index=False)
                elif output_format == 'parquet':
                    df.to_parquet(filepath, index=False)
                elif output_format == 'json':
                    df.to_json(filepath, orient='records', date_format='iso')
                    
            except Exception as e:
                logger.error(f"Error processing data for {ticker}: {str(e)}")
    
    # Print results
    click.echo(f"\nDownload completed!")
    click.echo(f"Total tickers: {results['total']}")
    click.echo(f"Successful: {results['successful']}")
    click.echo(f"Failed: {results['failed']}")
    
    if results['failed_tickers']:
        click.echo(f"\nFailed tickers: {', '.join(results['failed_tickers'])}")


@cli.command()
@click.option('--country', help='Country code (us, uk, jp, de, cn)')
def list_tickers(country):
    """List available tickers"""
    
    if country:
        tickers = get_country_tickers(country)
        if tickers:
            click.echo(f"Tickers for {country.upper()}:")
            for ticker in tickers:
                click.echo(f"  {ticker}")
        else:
            click.echo(f"No tickers found for country {country}")
    else:
        countries = get_available_countries()
        if countries:
            click.echo("Available countries:")
            for c in countries:
                tickers = get_country_tickers(c)
                click.echo(f"  {c.upper()}: {len(tickers)} tickers")
        else:
            click.echo("No ticker files found")


@cli.command()
@click.argument('ticker')
@click.option('--start-date', help='Start date in YYYY-MM-DD format')
@click.option('--end-date', help='End date in YYYY-MM-DD format')
@click.option('--days', default=30, help='Number of days to look back (default: 30)')
def info(ticker, start_date, end_date, days):
    """Get information about a specific ticker"""
    
    downloader = ParallelDownloader()
    
    # Get ticker info
    ticker_info = downloader.get_ticker_info(ticker)
    
    if ticker_info:
        click.echo(f"\nInformation for {ticker}:")
        click.echo(f"Name: {ticker_info.get('longName', 'N/A')}")
        click.echo(f"Sector: {ticker_info.get('sector', 'N/A')}")
        click.echo(f"Industry: {ticker_info.get('industry', 'N/A')}")
        click.echo(f"Market Cap: {ticker_info.get('marketCap', 'N/A')}")
        click.echo(f"Currency: {ticker_info.get('currency', 'N/A')}")
        click.echo(f"Exchange: {ticker_info.get('exchange', 'N/A')}")
    else:
        click.echo(f"No information found for ticker {ticker}")


@cli.command()
def version():
    """Show version information"""
    click.echo("yfdownloader version 1.0.0")


if __name__ == '__main__':
    cli()