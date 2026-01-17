"""
Additional CLI commands for Yahoo Finance downloader
"""

import click
import pandas as pd
from pathlib import Path
import sys
from typing import List

# Add the parent directory to the path to import core modules
sys.path.append(str(Path(__file__).parent.parent))

from core.processor import DataProcessor
from core.utils import merge_csv_files, get_file_size, format_file_size


@click.group()
def data():
    """Data processing and analysis commands"""
    pass


@data.command()
@click.argument('input_dir', type=click.Path(exists=True))
@click.argument('output_file', type=click.Path())
@click.option('--remove-duplicates', is_flag=True, default=True, help='Remove duplicate rows')
@click.option('--format', 'output_format', default='csv', type=click.Choice(['csv', 'parquet', 'json']), help='Output format')
def merge(input_dir, output_file, remove_duplicates, output_format):
    """Merge all data files in a directory"""
    
    input_path = Path(input_dir)
    
    # Find all CSV files
    if output_format == 'csv':
        files = list(input_path.glob("*.csv"))
    elif output_format == 'parquet':
        files = list(input_path.glob("*.parquet"))
    elif output_format == 'json':
        files = list(input_path.glob("*.json"))
    
    if not files:
        click.echo(f"No {output_format} files found in {input_dir}")
        return
    
    click.echo(f"Found {len(files)} files to merge")
    
    # Merge files
    if output_format == 'csv':
        success = merge_csv_files([str(f) for f in files], output_file, remove_duplicates)
    else:
        # For non-CSV formats, we'll use pandas
        all_data = []
        for file in files:
            try:
                if output_format == 'parquet':
                    df = pd.read_parquet(file)
                elif output_format == 'json':
                    df = pd.read_json(file)
                all_data.append(df)
            except Exception as e:
                click.echo(f"Error reading {file}: {str(e)}")
                continue
        
        if not all_data:
            click.echo("No valid data to merge")
            return
        
        merged_df = pd.concat(all_data, ignore_index=True)
        
        if remove_duplicates:
            merged_df = merged_df.drop_duplicates()
        
        try:
            if output_format == 'parquet':
                merged_df.to_parquet(output_file, index=False)
            elif output_format == 'json':
                merged_df.to_json(output_file, orient='records', date_format='iso')
            success = True
        except Exception as e:
            click.echo(f"Error saving merged data: {str(e)}")
            success = False
    
    if success:
        file_size = get_file_size(output_file)
        click.echo(f"Successfully merged {len(files)} files into {output_file}")
        click.echo(f"Output file size: {format_file_size(file_size)}")
    else:
        click.echo("Failed to merge files")


@data.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--add-indicators', is_flag=True, help='Add technical indicators')
@click.option('--validate', is_flag=True, help='Validate and clean data')
@click.option('--returns', is_flag=True, help='Calculate returns')
@click.option('--resample', help='Resample frequency (D, W, M)')
@click.option('--output', help='Output file path (default: overwrite input)')
def process(input_file, add_indicators, validate, returns, resample, output):
    """Process and analyze downloaded data"""
    
    # Read input file
    try:
        if input_file.endswith('.csv'):
            df = pd.read_csv(input_file)
        elif input_file.endswith('.parquet'):
            df = pd.read_parquet(input_file)
        elif input_file.endswith('.json'):
            df = pd.read_json(input_file)
        else:
            click.echo(f"Unsupported file format: {input_file}")
            return
    except Exception as e:
        click.echo(f"Error reading file {input_file}: {str(e)}")
        return
    
    click.echo(f"Loaded data with {len(df)} rows and {len(df.columns)} columns")
    
    # Initialize processor
    processor = DataProcessor()
    
    # Process data
    if validate:
        df = processor.validate_data(df)
        click.echo("Data validated and cleaned")
    
    if add_indicators:
        df = processor.add_technical_indicators(df)
        click.echo("Technical indicators added")
    
    if returns:
        df = processor.calculate_returns(df)
        click.echo("Returns calculated")
    
    if resample:
        df = processor.resample_data(df, resample)
        click.echo(f"Data resampled to {resample} frequency")
    
    # Save processed data
    output_file = output or input_file
    try:
        if output_file.endswith('.csv'):
            df.to_csv(output_file, index=False)
        elif output_file.endswith('.parquet'):
            df.to_parquet(output_file, index=False)
        elif output_file.endswith('.json'):
            df.to_json(output_file, orient='records', date_format='iso')
        
        click.echo(f"Processed data saved to {output_file}")
    except Exception as e:
        click.echo(f"Error saving processed data: {str(e)}")


@data.command()
@click.argument('input_file', type=click.Path(exists=True))
def summary(input_file):
    """Show summary statistics for data file"""
    
    # Read input file
    try:
        if input_file.endswith('.csv'):
            df = pd.read_csv(input_file)
        elif input_file.endswith('.parquet'):
            df = pd.read_parquet(input_file)
        elif input_file.endswith('.json'):
            df = pd.read_json(input_file)
        else:
            click.echo(f"Unsupported file format: {input_file}")
            return
    except Exception as e:
        click.echo(f"Error reading file {input_file}: {str(e)}")
        return
    
    # Get summary
    processor = DataProcessor()
    summary = processor.get_data_summary(df)
    
    if summary:
        click.echo(f"\nSummary for {input_file}:")
        click.echo(f"Total records: {summary['total_records']:,}")
        click.echo(f"Unique tickers: {summary['unique_tickers']}")
        click.echo(f"Date range: {summary['date_range']['start']} to {summary['date_range']['end']}")
        click.echo(f"Price range: ${summary['price_stats']['min_close']:.2f} - ${summary['price_stats']['max_close']:.2f}")
        click.echo(f"Average price: ${summary['price_stats']['mean_close']:.2f}")
        click.echo(f"Total volume: {summary['volume_stats']['total_volume']:,}")
        click.echo(f"Average volume: {summary['volume_stats']['mean_volume']:,.0f}")
    else:
        click.echo("No data to summarize")


@data.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--start-date', help='Start date in YYYY-MM-DD format')
@click.option('--end-date', help='End date in YYYY-MM-DD format')
@click.option('--output', help='Output file path')
def filter(input_file, start_date, end_date, output):
    """Filter data by date range"""
    
    if not start_date or not end_date:
        click.echo("Both --start-date and --end-date are required")
        return
    
    # Read input file
    try:
        if input_file.endswith('.csv'):
            df = pd.read_csv(input_file)
        elif input_file.endswith('.parquet'):
            df = pd.read_parquet(input_file)
        elif input_file.endswith('.json'):
            df = pd.read_json(input_file)
        else:
            click.echo(f"Unsupported file format: {input_file}")
            return
    except Exception as e:
        click.echo(f"Error reading file {input_file}: {str(e)}")
        return
    
    # Filter data
    processor = DataProcessor()
    filtered_df = processor.filter_by_date_range(df, start_date, end_date)
    
    click.echo(f"Filtered {len(df)} rows to {len(filtered_df)} rows")
    
    # Save filtered data
    output_file = output or f"filtered_{Path(input_file).name}"
    try:
        if output_file.endswith('.csv'):
            filtered_df.to_csv(output_file, index=False)
        elif output_file.endswith('.parquet'):
            filtered_df.to_parquet(output_file, index=False)
        elif output_file.endswith('.json'):
            filtered_df.to_json(output_file, orient='records', date_format='iso')
        
        click.echo(f"Filtered data saved to {output_file}")
    except Exception as e:
        click.echo(f"Error saving filtered data: {str(e)}")