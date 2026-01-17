"""
Data processing utilities for Yahoo Finance data
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DataProcessor:
    """Process and validate Yahoo Finance data"""
    
    @staticmethod
    def validate_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        Validate and clean downloaded data
        
        Args:
            df: Raw DataFrame from Yahoo Finance
            
        Returns:
            Cleaned DataFrame
        """
        if df.empty:
            return df
        
        # Check required columns
        required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.warning(f"Missing columns: {missing_columns}")
        
        # Remove rows with missing OHLCV data
        df = df.dropna(subset=['open', 'high', 'low', 'close', 'volume'])
        
        # Remove duplicate dates
        df = df.drop_duplicates(subset=['date', 'ticker'])
        
        # Sort by date and ticker
        df = df.sort_values(['ticker', 'date'])
        
        # Validate OHLC relationships
        # High should be >= Open, Low, Close
        # Low should be <= Open, High, Close
        invalid_high = df['high'] < df[['open', 'low', 'close']].max(axis=1)
        invalid_low = df['low'] > df[['open', 'high', 'close']].min(axis=1)
        
        if invalid_high.any() or invalid_low.any():
            logger.warning(f"Found {invalid_high.sum()} invalid high prices and {invalid_low.sum()} invalid low prices")
        
        # Volume should be non-negative
        negative_volume = df['volume'] < 0
        if negative_volume.any():
            logger.warning(f"Found {negative_volume.sum()} rows with negative volume")
            df.loc[negative_volume, 'volume'] = 0
        
        return df
    
    @staticmethod
    def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Add common technical indicators
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with technical indicators added
        """
        if df.empty:
            return df
        
        df = df.copy()
        
        # Sort by ticker and date
        df = df.sort_values(['ticker', 'date'])
        
        # Group by ticker to calculate indicators per stock
        for ticker, group in df.groupby('ticker'):
            # Moving averages
            group['ma_5'] = group['close'].rolling(window=5).mean()
            group['ma_10'] = group['close'].rolling(window=10).mean()
            group['ma_20'] = group['close'].rolling(window=20).mean()
            group['ma_50'] = group['close'].rolling(window=50).mean()
            
            # RSI (Relative Strength Index)
            delta = group['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            group['rsi'] = 100 - (100 / (1 + rs))
            
            # MACD
            exp1 = group['close'].ewm(span=12, adjust=False).mean()
            exp2 = group['close'].ewm(span=26, adjust=False).mean()
            group['macd'] = exp1 - exp2
            group['macd_signal'] = group['macd'].ewm(span=9, adjust=False).mean()
            group['macd_histogram'] = group['macd'] - group['macd_signal']
            
            # Bollinger Bands
            group['bb_middle'] = group['close'].rolling(window=20).mean()
            bb_std = group['close'].rolling(window=20).std()
            group['bb_upper'] = group['bb_middle'] + (bb_std * 2)
            group['bb_lower'] = group['bb_middle'] - (bb_std * 2)
            
            # Update the main dataframe
            df.loc[group.index, group.columns] = group
        
        return df
    
    @staticmethod
    def resample_data(
        df: pd.DataFrame,
        frequency: str = 'D'
    ) -> pd.DataFrame:
        """
        Resample data to different frequency
        
        Args:
            df: DataFrame with OHLCV data
            frequency: Resampling frequency (D, W, M)
            
        Returns:
            Resampled DataFrame
        """
        if df.empty:
            return df
        
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # Group by ticker and resample
        resampled_groups = []
        for ticker, group in df.groupby('ticker'):
            resampled = group.resample(frequency).agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
            
            resampled['ticker'] = ticker
            resampled_groups.append(resampled)
        
        if resampled_groups:
            result = pd.concat(resampled_groups)
            result.reset_index(inplace=True)
            return result
        else:
            return pd.DataFrame()
    
    @staticmethod
    def merge_dataframes(
        dataframes: List[pd.DataFrame],
        on: str = 'date'
    ) -> pd.DataFrame:
        """
        Merge multiple DataFrames
        
        Args:
            dataframes: List of DataFrames to merge
            on: Column to merge on
            
        Returns:
            Merged DataFrame
        """
        if not dataframes:
            return pd.DataFrame()
        
        result = dataframes[0]
        for df in dataframes[1:]:
            result = pd.merge(result, df, on=on, how='outer')
        
        return result
    
    @staticmethod
    def calculate_returns(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate returns for each ticker
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with returns added
        """
        if df.empty:
            return df
        
        df = df.copy()
        df = df.sort_values(['ticker', 'date'])
        
        # Calculate daily returns
        df['daily_return'] = df.groupby('ticker')['close'].pct_change()
        
        # Calculate log returns
        df['log_return'] = np.log(df['close'] / df['close'].shift(1))
        
        # Calculate cumulative returns
        df['cumulative_return'] = df.groupby('ticker')['daily_return'].cumsum()
        
        return df
    
    @staticmethod
    def filter_by_date_range(
        df: pd.DataFrame,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        Filter DataFrame by date range
        
        Args:
            df: DataFrame with date column
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Filtered DataFrame
        """
        if df.empty:
            return df
        
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        
        mask = (df['date'] >= start_date) & (df['date'] <= end_date)
        return df[mask]
    
    @staticmethod
    def get_data_summary(df: pd.DataFrame) -> Dict:
        """
        Get summary statistics for the data
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Dictionary with summary statistics
        """
        if df.empty:
            return {}
        
        summary = {
            'total_records': len(df),
            'unique_tickers': df['ticker'].nunique(),
            'date_range': {
                'start': df['date'].min(),
                'end': df['date'].max()
            },
            'price_stats': {
                'min_close': df['close'].min(),
                'max_close': df['close'].max(),
                'mean_close': df['close'].mean(),
                'median_close': df['close'].median()
            },
            'volume_stats': {
                'total_volume': df['volume'].sum(),
                'mean_volume': df['volume'].mean(),
                'median_volume': df['volume'].median()
            }
        }
        
        return summary