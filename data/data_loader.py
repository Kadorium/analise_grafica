import pandas as pd
import numpy as np
import os
from datetime import datetime
import csv
import locale

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
            # First, detect if this is a European style CSV by checking first few lines
            with open(self.file_path, 'r', encoding='utf-8', errors='replace') as f:
                sample = f.read(2048)
                
                # Check for semicolons as separators and comma decimal separators
                has_semicolons = ';' in sample
                has_comma_decimals = any(c.isdigit() and ',' in c and c.replace(',', '').replace('.', '').isdigit() 
                                          for c in sample.split() if c)
                
                print(f"Detected CSV format - Semicolons: {has_semicolons}, Comma decimals: {has_comma_decimals}")
                
                # Try to detect the date format by checking patterns
                date_format = None
                for line in sample.split('\n')[:5]:  # Check first 5 lines
                    parts = line.split(';' if has_semicolons else ',')
                    if len(parts) > 1:
                        potential_date = parts[0].strip()
                        if '/' in potential_date:
                            if len(potential_date.split('/')[2]) == 2:  # YY format
                                date_format = '%d/%m/%y' if len(potential_date.split('/')[0]) == 2 else '%m/%d/%y'
                            else:  # YYYY format
                                date_format = '%d/%m/%Y' if len(potential_date.split('/')[0]) == 2 else '%m/%d/%Y'
                            print(f"Detected date format: {date_format}")
                            break
            
            # For European-style CSVs (semicolon separator, comma as decimal)
            if has_semicolons:
                print("Loading European CSV format (semicolon separator)")
                
                # Read with appropriate parameters for European format
                self.data = pd.read_csv(
                    self.file_path,
                    sep=';',
                    decimal=',',  # Use comma as decimal separator
                    engine='python',
                    on_bad_lines='skip',
                    skipinitialspace=True,
                    encoding='utf-8',
                    encoding_errors='replace'
                )
                
                # Clean up empty columns
                for col in self.data.columns:
                    if col.lower().startswith('unnamed'):
                        if self.data[col].isna().all():
                            self.data = self.data.drop(columns=[col])
                
            else:
                # Try reading with our standard approach
                dialect = csv.Sniffer().sniff(sample)
                delimiter = dialect.delimiter
                
                # Try reading with the detected delimiter
                self.data = pd.read_csv(
                    self.file_path,
                    delimiter=delimiter,
                    engine='python',
                    on_bad_lines='skip',
                    quotechar='"',
                    skipinitialspace=True,
                    encoding='utf-8',
                    encoding_errors='replace'
                )
            
            # If file has thousands of dates, ensure efficient processing
            if len(self.data) > 10000:
                print(f"Large dataset detected: {len(self.data)} rows. Optimizing...")
            
            # Store detected date format for later use
            self.detected_date_format = date_format
            
            return self.data
            
        except Exception as e:
            # If first attempt fails, try alternative approaches
            try:
                print(f"Initial read failed: {str(e)}. Trying alternative approaches...")
                
                # Try to read with pandas' auto-detection
                self.data = pd.read_csv(
                    self.file_path,
                    sep=None,  # Let pandas detect the separator
                    engine='python',
                    on_bad_lines='skip',
                )
                print("Successfully loaded data with auto-detected separator.")
                return self.data
                
            except Exception as e2:
                # As a last resort, try reading with more flexibility
                try:
                    # Try to read file with very flexible settings
                    self.data = pd.read_csv(
                        self.file_path,
                        sep=None,
                        header=None,  # Assume no header if everything else fails
                        engine='python',
                        on_bad_lines='skip',
                    )
                    
                    # If successful, generate default column names
                    if len(self.data.columns) >= 6:
                        # Rename columns to expected format
                        default_names = ['date', 'open', 'high', 'low', 'close', 'volume']
                        rename_dict = {i: name for i, name in enumerate(default_names) if i < len(self.data.columns)}
                        self.data.rename(columns=rename_dict, inplace=True)
                        
                        print("Loaded data with default column names. Please verify column mapping.")
                        return self.data
                    else:
                        raise ValueError("CSV format doesn't match expected structure")
                        
                except Exception as e3:
                    # Try one more time with 'c' engine for large files
                    try:
                        print("Trying with C engine for large files...")
                        self.data = pd.read_csv(
                            self.file_path,
                            engine='c',  # Faster C engine
                            low_memory=False,  # Compatible with C engine
                            on_bad_lines='error',  # Default for C engine
                            skipinitialspace=True,
                            encoding='utf-8',
                            encoding_errors='replace'
                        )
                        print("Successfully loaded with C engine.")
                        return self.data
                    except Exception as e4:
                        raise Exception(f"All attempts to read the CSV file failed:\n"
                                      f"1. {str(e)}\n"
                                      f"2. {str(e2)}\n"
                                      f"3. {str(e3)}\n"
                                      f"4. {str(e4)}")
    
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
        
        # Remove any empty unnamed columns
        unnamed_cols = [col for col in self.data.columns if 'unnamed' in col.lower()]
        if unnamed_cols:
            for col in unnamed_cols:
                # Check if column is empty (all NaN)
                if self.data[col].isna().all():
                    self.data = self.data.drop(columns=[col])
        
        # Check for required columns
        required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in self.data.columns]
        
        if missing_columns:
            # Try to identify columns by position if names don't match
            if len(self.data.columns) >= 6:
                print(f"Missing columns: {', '.join(missing_columns)}. Attempting to map columns by position...")
                
                # Create a mapping from position to expected column names
                column_mapping = {}
                for i, req_col in enumerate(required_columns):
                    if i < len(self.data.columns) and req_col not in self.data.columns:
                        column_mapping[self.data.columns[i]] = req_col
                
                # Rename columns
                if column_mapping:
                    self.data.rename(columns=column_mapping, inplace=True)
                    
                    # Check again for missing columns
                    missing_columns = [col for col in required_columns if col not in self.data.columns]
                    
                    if missing_columns:
                        raise ValueError(f"Still missing required columns after mapping: {', '.join(missing_columns)}")
                    else:
                        print("Successfully mapped columns by position.")
            else:
                raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Convert date to datetime with error handling
        try:
            # If we detected a specific date format during loading, use it
            if hasattr(self, 'detected_date_format') and self.detected_date_format:
                print(f"Using detected date format: {self.detected_date_format}")
                self.data['date'] = pd.to_datetime(self.data['date'], format=self.detected_date_format, errors='coerce')
            else:
                self.data['date'] = pd.to_datetime(self.data['date'], errors='coerce')
                
            # Check if dates were properly parsed
            if self.data['date'].isna().all():
                raise ValueError("Failed to parse any dates with the detected format")
                
        except Exception as e:
            print(f"Error converting date column: {str(e)}. Trying different formats...")
            
            # Try different date formats
            date_formats = ['%d/%m/%Y', '%d/%m/%y', '%m/%d/%Y', '%m/%d/%y', '%Y-%m-%d', '%Y/%m/%d']
            success = False
            
            for date_format in date_formats:
                try:
                    print(f"Trying date format: {date_format}")
                    self.data['date'] = pd.to_datetime(self.data['date'], format=date_format, errors='coerce')
                    if not self.data['date'].isna().all():
                        print(f"Successfully parsed dates with format: {date_format}")
                        success = True
                        break
                except Exception as date_err:
                    print(f"Failed with format {date_format}: {str(date_err)}")
                    continue
                    
            if not success:
                print("WARNING: Could not parse dates with any common format.")
        
        # Ensure numeric types for OHLCV with error handling for different formats
        for col in ['open', 'high', 'low', 'close', 'volume']:
            # Replace commas in numeric values if they're being used as decimal separators
            if self.data[col].dtype == 'object':
                # European format: replace comma with dot for decimal places
                self.data[col] = self.data[col].astype(str).str.replace(',', '.')
                
            # Convert to numeric
            self.data[col] = pd.to_numeric(self.data[col], errors='coerce')
            
        # Handle missing values
        before_rows = len(self.data)
        self.data.dropna(inplace=True)
        after_rows = len(self.data)
        
        if before_rows > after_rows:
            print(f"Removed {before_rows - after_rows} rows with missing values.")
            
        # If all data was dropped, this is a serious error
        if after_rows == 0:
            print("ERROR: All data rows were dropped after cleaning!")
            print("Most likely causes:")
            print("1. Date format mismatch - Could not parse any dates")
            print("2. Number format issues - Cannot convert price/volume data to numbers")
            print("3. Missing values in critical columns")
            print("\nOriginal data sample:")
            print(self.data.head(3))
        
        # Sort by date
        self.data.sort_values('date', inplace=True)
        
        # Add a message for large datasets
        if len(self.data) > 1000:
            print(f"Successfully processed {len(self.data)} dates.")
        
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