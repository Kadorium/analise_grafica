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
        self.multi_asset_data = {}
        
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

    def load_multi_asset_excel(self, file_path=None):
        """
        Load data from a multi-sheet Excel file where each sheet represents a different asset.
        
        Args:
            file_path (str, optional): Path to the Excel file. If None, uses the instance's file_path.
            
        Returns:
            dict: A dictionary where keys are asset names (sheet names) and values are DataFrames.
        """
        if file_path:
            self.file_path = file_path
            
        if not self.file_path:
            raise ValueError("File path not provided")
        
        # Check if file exists
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Excel file not found at {self.file_path}")
        
        try:
            # Get all sheet names
            excel_file = pd.ExcelFile(self.file_path)
            sheet_names = excel_file.sheet_names
            
            if not sheet_names:
                raise ValueError("Excel file does not contain any sheets")
            
            # Required columns for each asset sheet
            required_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'VWAP', 'Volume']
            
            # Process each sheet
            self.multi_asset_data = {}
            date_min = None
            date_max = None
            
            for sheet_name in sheet_names:
                try:
                    # Read the sheet
                    sheet_data = pd.read_excel(excel_file, sheet_name=sheet_name)
                    
                    # Check for required columns (case-insensitive)
                    sheet_columns = [col.lower() for col in sheet_data.columns]
                    required_lower = [col.lower() for col in required_columns]
                    
                    # Find missing columns
                    missing_columns = []
                    for i, req_col in enumerate(required_lower):
                        if req_col not in sheet_columns:
                            missing_columns.append(required_columns[i])
                    
                    if missing_columns:
                        raise ValueError(f"Missing required column(s) in sheet '{sheet_name}': {', '.join(missing_columns)}")
                    
                    # Standardize column names to lowercase
                    column_mapping = {col: col.lower() for col in sheet_data.columns}
                    sheet_data.rename(columns=column_mapping, inplace=True)
                    
                    # Convert date column to datetime
                    if 'date' in sheet_data.columns:
                        sheet_data['date'] = pd.to_datetime(sheet_data['date'], errors='coerce')
                        # Drop rows with invalid dates
                        sheet_data = sheet_data.dropna(subset=['date'])
                        
                        # Update global date range
                        sheet_min = sheet_data['date'].min()
                        sheet_max = sheet_data['date'].max()
                        
                        if date_min is None or sheet_min < date_min:
                            date_min = sheet_min
                        
                        if date_max is None or sheet_max > date_max:
                            date_max = sheet_max
                    
                    # Ensure numeric columns are numeric
                    numeric_columns = ['open', 'high', 'low', 'close', 'vwap', 'volume']
                    for col in numeric_columns:
                        if col in sheet_data.columns:
                            sheet_data[col] = pd.to_numeric(sheet_data[col], errors='coerce')
                    
                    # Drop rows with NA values in essential columns
                    sheet_data = sheet_data.dropna(subset=['open', 'high', 'low', 'close', 'volume'])
                    
                    # Store processed data
                    self.multi_asset_data[sheet_name] = sheet_data
                    
                except Exception as e:
                    print(f"Error processing sheet '{sheet_name}': {str(e)}")
                    # Continue processing other sheets even if one fails
            
            # Check if we successfully loaded any data
            if not self.multi_asset_data:
                raise ValueError("Could not load any valid data from Excel sheets")
            
            # Store overall date range
            self.multi_asset_date_range = {
                'start': date_min.strftime('%Y-%m-%d') if date_min else None,
                'end': date_max.strftime('%Y-%m-%d') if date_max else None
            }
            
            return self.multi_asset_data
            
        except Exception as e:
            raise Exception(f"Failed to load multi-asset Excel file: {str(e)}")
    
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
                except Exception:
                    continue
            
            if not success:
                print("Failed to parse dates with common formats. Attempting last resort method...")
                try:
                    # Try a more flexible approach by converting string to datetime objects
                    if self.data['date'].dtype == object:  # If it's string type
                        # Parse each date individually with multiple formats
                        parsed_dates = []
                        for date_str in self.data['date']:
                            try:
                                parsed_date = None
                                for fmt in date_formats:
                                    try:
                                        parsed_date = datetime.strptime(str(date_str).strip(), fmt)
                                        break
                                    except:
                                        continue
                                parsed_dates.append(parsed_date)
                            except:
                                parsed_dates.append(None)
                                
                        self.data['date'] = parsed_dates
                        self.data['date'] = pd.to_datetime(self.data['date'])
                        
                        if not self.data['date'].isna().all():
                            print("Successfully parsed dates with manual approach")
                            success = True
                    
                except Exception as e:
                    print(f"Final date parsing attempt failed: {str(e)}")
                
                if not success:
                    raise ValueError("Could not parse date column after trying multiple formats")
        
        # Convert numeric columns
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if col in self.data.columns:
                # If column has string type, try to clean it first
                if self.data[col].dtype == object:
                    # Replace comma with dot for decimal separator
                    self.data[col] = self.data[col].astype(str).str.replace(',', '.')
                    
                # Convert to numeric
                self.data[col] = pd.to_numeric(self.data[col], errors='coerce')
        
        # Sort by date
        self.data = self.data.sort_values('date')
        
        # Drop rows with missing values in key columns
        self.data = self.data.dropna(subset=numeric_columns)
        
        # Reset index
        self.data = self.data.reset_index(drop=True)
        
        return self.data
    
    def save_processed_data(self, output_path=None):
        """
        Save the processed data to a CSV file.
        
        Args:
            output_path (str, optional): Path to save the CSV file. 
                If None, uses the instance's file_path with '_processed' appended.
                
        Returns:
            str: The path where the data was saved.
        """
        if self.data is None:
            raise ValueError("No data to save. Load and clean data first.")
        
        if output_path is None:
            if self.file_path:
                # Create output path by appending '_processed' to the original filename
                file_dir, file_name = os.path.split(self.file_path)
                file_base, file_ext = os.path.splitext(file_name)
                output_path = os.path.join(file_dir, f"{file_base}_processed{file_ext}")
            else:
                # Default to a standard name if no file_path is set
                output_path = "data_processed.csv"
        
        # Ensure date is formatted as ISO date strings
        output_data = self.data.copy()
        if 'date' in output_data.columns and pd.api.types.is_datetime64_any_dtype(output_data['date']):
            output_data['date'] = output_data['date'].dt.strftime('%Y-%m-%d')
        
        # Save to CSV
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        output_data.to_csv(output_path, index=False)
        print(f"Data saved to {output_path}")
        
        return output_path
    
    def load_processed_data(self, file_path=None):
        """
        Load previously processed data from a CSV file.
        
        Args:
            file_path (str, optional): Path to the processed CSV file. 
                If None, tries to use a default path based on the instance's file_path.
                
        Returns:
            pandas.DataFrame: The loaded processed data.
        """
        if file_path is None:
            if self.file_path:
                # Create input path by appending '_processed' to the original filename
                file_dir, file_name = os.path.split(self.file_path)
                file_base, file_ext = os.path.splitext(file_name)
                file_path = os.path.join(file_dir, f"{file_base}_processed{file_ext}")
            else:
                raise ValueError("No file path provided.")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Processed data file not found: {file_path}")
        
        # Load the processed data
        self.data = pd.read_csv(file_path)
        
        # Convert date to datetime
        if 'date' in self.data.columns:
            self.data['date'] = pd.to_datetime(self.data['date'])
        
        return self.data
    
    def get_data_range(self, start_date=None, end_date=None):
        """
        Get a slice of the data within a specified date range.
        
        Args:
            start_date (str, optional): Start date in YYYY-MM-DD format.
            end_date (str, optional): End date in YYYY-MM-DD format.
            
        Returns:
            pandas.DataFrame: Filtered data within the specified date range.
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_csv() first.")
        
        # Make a copy of the data to avoid modifying the original
        filtered_data = self.data.copy()
        
        # Convert date strings to datetime if provided
        if start_date:
            start_date = pd.to_datetime(start_date)
        
        if end_date:
            end_date = pd.to_datetime(end_date)
        
        # Filter by start date
        if start_date:
            filtered_data = filtered_data[filtered_data['date'] >= start_date]
        
        # Filter by end date
        if end_date:
            filtered_data = filtered_data[filtered_data['date'] <= end_date]
        
        return filtered_data 