import pandas as pd
import numpy as np
import os
from datetime import datetime

class DataLoader:
    """
    A class for loading, cleaning, and standardizing financial data.
    """
    
    def __init__(self, file_path=None):
        """
        Initialize the DataLoader with an optional file path.
        
        Args:
            file_path (str, optional): Path to the CSV file. Defaults to None.
        """
        self.file_path = file_path
        self.data = None
        
    def load_csv(self, file_path=None):
        """
        Load data from a CSV file.
        
        Args:
            file_path (str, optional): Path to the CSV file. If None, uses the instance's file_path.
            
        Returns:
            pandas.DataFrame: The loaded data.
        """
        if file_path:
            self.file_path = file_path
            
        if not self.file_path:
            raise ValueError("File path not provided")
            
        try:
            self.data = pd.read_csv(self.file_path)
            return self.data
        except Exception as e:
            raise Exception(f"Error loading CSV file: {str(e)}")
    
    def clean_data(self):
        """
        Clean the data by handling missing values and ensuring numeric types.
        
        Returns:
            pandas.DataFrame: The cleaned data.
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_csv() first.")
            
        # Convert column names to lowercase for consistency
        self.data.columns = [col.lower() for col in self.data.columns]
        
        # Check for required columns
        required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in self.data.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Convert date to datetime
        self.data['date'] = pd.to_datetime(self.data['date'])
        
        # Ensure numeric types for OHLCV
        for col in ['open', 'high', 'low', 'close', 'volume']:
            self.data[col] = pd.to_numeric(self.data[col], errors='coerce')
            
        # Handle missing values
        self.data.dropna(inplace=True)
        
        # Sort by date
        self.data.sort_values('date', inplace=True)
        
        return self.data
    
    def save_processed_data(self, output_path=None):
        """
        Save the processed data to a pickle file.
        
        Args:
            output_path (str, optional): Path to save the pickle file. 
                                        If None, uses 'data/clean_data.pkl'.
        
        Returns:
            str: Path to the saved file.
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_csv() first.")
            
        if output_path is None:
            output_path = os.path.join('data', 'clean_data.pkl')
            
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save to pickle
        self.data.to_pickle(output_path)
        
        return output_path
    
    def load_processed_data(self, file_path=None):
        """
        Load data from a pickle file.
        
        Args:
            file_path (str, optional): Path to the pickle file.
                                      If None, uses 'data/clean_data.pkl'.
        
        Returns:
            pandas.DataFrame: The loaded data.
        """
        if file_path is None:
            file_path = os.path.join('data', 'clean_data.pkl')
            
        try:
            self.data = pd.read_pickle(file_path)
            return self.data
        except Exception as e:
            raise Exception(f"Error loading pickle file: {str(e)}")
            
    def get_data_range(self, start_date=None, end_date=None):
        """
        Get data within a specific date range.
        
        Args:
            start_date (str, optional): Start date in format 'YYYY-MM-DD'.
            end_date (str, optional): End date in format 'YYYY-MM-DD'.
            
        Returns:
            pandas.DataFrame: Data within the specified range.
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_csv() or load_processed_data() first.")
            
        data = self.data.copy()
        
        if start_date:
            start_date = pd.to_datetime(start_date)
            data = data[data['date'] >= start_date]
            
        if end_date:
            end_date = pd.to_datetime(end_date)
            data = data[data['date'] <= end_date]
            
        return data 