import os
import pandas as pd
import numpy as np
from datetime import datetime
import csv
import sys
import traceback
import re

def arrange_data_file(input_file_path, output_dir="data", verbose=True):
    """
    Process input files (CSV, XLS, XLSX) and convert them to a standardized format.
    
    Args:
        input_file_path (str): Path to the input file
        output_dir (str): Directory to save the arranged file (default: 'data')
        verbose (bool): Whether to print detailed logs (default: True)
        
    Returns:
        str: Path to the arranged file
    """
    if verbose:
        print(f"Arranging file: {input_file_path}")
    
    # Make sure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate output filename
    file_name = os.path.basename(input_file_path)
    file_base, file_ext = os.path.splitext(file_name)
    output_file = os.path.join(output_dir, f"{file_base}_arranged.csv")
    
    # Create log container
    log_entries = [f"Processing file: {file_name}"]
    
    # Detect file type and load data
    file_ext = file_ext.lower()
    
    try:
        # --- LOADING DATA ---
        if file_ext == '.csv':
            try:
                # Try to detect CSV format by reading a sample
                with open(input_file_path, 'r', encoding='utf-8', errors='replace') as f:
                    sample = f.read(4096)  # Read a larger sample to better detect patterns
                    has_semicolons = ';' in sample
                    has_commas = ',' in sample
                    has_tabs = '\t' in sample
                    has_comma_decimals = any(re.search(r'\d+,\d+', c) for c in sample.split() if c)
                    has_dot_decimals = any(re.search(r'\d+\.\d+', c) for c in sample.split() if c)
                
                # Determine the most likely separator
                separator = ','
                decimal = '.'
                
                if has_semicolons and (not has_commas or has_comma_decimals):
                    separator = ';'
                    decimal = ',' if has_comma_decimals else '.'
                    if verbose:
                        print("Detected European CSV format (semicolon separator)")
                    log_entries.append("Detected European CSV format (semicolon separator)")
                elif has_tabs and not has_commas:
                    separator = '\t'
                    if verbose:
                        print("Detected tab-delimited file")
                    log_entries.append("Detected tab-delimited file")
                else:
                    if verbose:
                        print("Detected standard CSV format (comma separator)")
                    log_entries.append("Detected standard CSV format (comma separator)")
                
                # Try reading with the detected separator
                df = pd.read_csv(
                    input_file_path,
                    sep=separator,
                    decimal=decimal,
                    encoding='utf-8',
                    encoding_errors='replace',
                    on_bad_lines='skip'
                )
            except Exception as e:
                if verbose:
                    print(f"Error with standard loading, trying with more flexible options: {str(e)}")
                log_entries.append(f"Error with standard loading: {str(e)}")
                
                # Try with pandas' automatic separator detection
                df = pd.read_csv(
                    input_file_path,
                    sep=None,  # Auto-detect separator
                    engine='python',
                    on_bad_lines='skip',
                    encoding='utf-8',
                    encoding_errors='replace'
                )
        
        elif file_ext in ['.xls', '.xlsx']:
            if verbose:
                print(f"Loading Excel file: {file_ext}")
            log_entries.append(f"Loading Excel file: {file_ext}")
            
            # Try to load the first sheet by default, then try all sheets if that fails
            try:
                df = pd.read_excel(input_file_path)
            except Exception as e:
                if verbose:
                    print(f"Error loading first sheet, attempting to find valid data in other sheets: {str(e)}")
                log_entries.append(f"Error loading first sheet: {str(e)}")
                
                # Try each sheet until we find one with valid data
                xls = pd.ExcelFile(input_file_path)
                sheet_names = xls.sheet_names
                
                for sheet in sheet_names:
                    try:
                        df = pd.read_excel(input_file_path, sheet_name=sheet)
                        if len(df) > 0 and len(df.columns) >= 5:  # Reasonable minimum for OHLCV data
                            if verbose:
                                print(f"Successfully loaded data from sheet: {sheet}")
                            log_entries.append(f"Successfully loaded data from sheet: {sheet}")
                            break
                    except:
                        continue
                else:
                    raise ValueError(f"Could not find valid data in any sheet of the Excel file")
        
        else:
            raise ValueError(f"Unsupported file format: {file_ext}. Supported formats are: CSV, XLS, XLSX")
        
        # --- INITIAL DATA VALIDATION ---
        if verbose:
            print(f"Successfully loaded file with {len(df)} rows and {len(df.columns)} columns")
            print(f"Column names: {list(df.columns)}")
        
        log_entries.append(f"Raw data shape: {df.shape}")
        log_entries.append(f"Original column names: {list(df.columns)}")
        
        # Store original row count for comparison
        original_row_count = len(df)
        
        # Handle empty dataframe
        if len(df) == 0:
            raise ValueError("The file contains no data rows")
        
        # Save a copy of the raw data for debug purposes
        raw_df = df.copy()
        
        # --- COLUMN MAPPING ---
        # Standardize column names (make lowercase)
        df.columns = [str(col).lower().strip() for col in df.columns]
        
        # Remove any empty unnamed columns
        unnamed_cols = [col for col in df.columns if 'unnamed' in str(col).lower()]
        for col in unnamed_cols:
            if df[col].isna().all():
                df = df.drop(columns=[col])
        
        if verbose:
            print(f"Cleaned column names: {list(df.columns)}")
        
        # Identify OHLCV columns based on common naming patterns
        required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        column_mapping = {}
        
        # Map exact matches
        for col in df.columns:
            for req_col in required_columns:
                if col == req_col or col == req_col[0]:  # Also match first letter (e.g. 'o' for 'open')
                    column_mapping[col] = req_col
                    break
        
        # Additional common patterns to try (expanded patterns)
        pattern_mapping = {
            'date': ['date', 'time', 'day', 'dt', 'timestamp', 'dates', 'datetime'],
            'open': ['open', 'opening', 'first', 'o', 'op', 'inicio', 'apertura', 'px_open', 'price_open'],
            'high': ['high', 'highest', 'max', 'h', 'hi', 'maximo', 'alto', 'px_high', 'price_high'],
            'low': ['low', 'lowest', 'min', 'l', 'lo', 'minimo', 'bajo', 'px_low', 'price_low'],
            'close': ['close', 'closing', 'last', 'c', 'cl', 'final', 'cierre', 'px_close', 'px_last', 'price_close', 'price_last', 'settle', 'settlement'],
            'volume': ['volume', 'vol', 'v', 'volumen', 'qty', 'quantity', 'size', 'vl']
        }
        
        # Apply expanded pattern mapping
        for req_col, patterns in pattern_mapping.items():
            if req_col not in column_mapping.values():
                for col in df.columns:
                    if any(pattern in col.lower() for pattern in patterns):
                        column_mapping[col] = req_col
                        break
        
        # Bloomberg and Yahoo Finance column mapping
        specialized_mapping = {
            # Bloomberg
            'px_open': 'open',
            'px_high': 'high',
            'px_low': 'low',
            'px_last': 'close',
            'eqy_weighted_avg_px': 'vwap',
            # Yahoo Finance
            'adj close': 'adj_close',
            'adj. close': 'adj_close',
            'adjusted close': 'adj_close'
        }
        
        for col in df.columns:
            col_lower = col.lower().strip()
            if col_lower in specialized_mapping and specialized_mapping[col_lower] not in column_mapping.values():
                column_mapping[col] = specialized_mapping[col_lower]
        
        # Attempt numerical column detection if still missing columns
        # If we find columns that are clearly numerical and in ascending order of value,
        # they might be OHLCV data
        if len(column_mapping) < 5:  # We're missing multiple columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if len(numeric_cols) >= 4:  # At least enough for OHLC
                # Try to identify columns by typical price relationships: high >= open/close >= low
                # First, get sample mean values to compare
                numeric_means = {col: df[col].mean() for col in numeric_cols if not df[col].isna().all()}
                sorted_cols = sorted(numeric_means.keys(), key=lambda x: numeric_means[x])
                
                if len(sorted_cols) >= 4:
                    # Lowest likely is low, highest likely is high
                    if 'low' not in column_mapping.values():
                        column_mapping[sorted_cols[0]] = 'low'
                    if 'high' not in column_mapping.values():
                        column_mapping[sorted_cols[-1]] = 'high'
                    
                    # For middle values, assign to open/close
                    remaining_middle = [c for c in sorted_cols[1:-1] if c not in column_mapping]
                    if len(remaining_middle) >= 2:
                        if 'open' not in column_mapping.values():
                            column_mapping[remaining_middle[0]] = 'open'
                        if 'close' not in column_mapping.values():
                            column_mapping[remaining_middle[-1]] = 'close'
        
        # If we still haven't found all columns, try by position if there are enough columns
        if len(column_mapping) < 6 and len(df.columns) >= 6:
            if verbose:
                print("Attempting to map columns by position...")
            log_entries.append("Attempting to map columns by position")
            
            # Common column order: Date, Open, High, Low, Close, Volume
            position_mapping = {}
            for i, req_col in enumerate(required_columns):
                if i < len(df.columns) and req_col not in column_mapping.values():
                    position_mapping[df.columns[i]] = req_col
            
            # Add the position mappings to our mapping dictionary
            column_mapping.update(position_mapping)
        
        if verbose:
            print(f"Column mapping: {column_mapping}")
        log_entries.append(f"Column mapping: {column_mapping}")
        
        # --- DATA TRANSFORMATION ---
        # Apply the column mapping
        df = df.rename(columns=column_mapping)
        
        # Check which columns we have mapped
        mapped_columns = set(column_mapping.values())
        required_columns_set = set(required_columns)
        
        # For completely missing columns, create them with default values
        # Rather than failing, we can fill with estimated values or defaults
        for col in required_columns:
            if col not in df.columns:
                if col == 'volume':
                    # Missing volume can be set to 0
                    df[col] = 0
                    log_entries.append(f"Created missing column: {col} with zeros")
                elif col == 'date':
                    # If date is missing, we can't really proceed
                    raise ValueError("Could not identify a date column, which is required")
                elif col == 'open' and 'close' in df.columns:
                    # Can use close as a substitute for missing open
                    df[col] = df['close']
                    log_entries.append(f"Created missing column: {col} using close values")
                elif col == 'high' and 'close' in df.columns:
                    # Use close as a base for high
                    df[col] = df['close']
                    log_entries.append(f"Created missing column: {col} using close values")
                elif col == 'low' and 'close' in df.columns:
                    # Use close as a base for low
                    df[col] = df['close']
                    log_entries.append(f"Created missing column: {col} using close values")
                elif col == 'close' and 'open' in df.columns:
                    # Use open as a substitute for missing close
                    df[col] = df['open']
                    log_entries.append(f"Created missing column: {col} using open values")
                else:
                    # If we can't make a reasonable estimate, might need to skip
                    log_entries.append(f"WARNING: Required column {col} is missing and cannot be estimated")
        
        # --- DATE PROCESSING ---
        # Store a copy of the original date column for reference
        if 'date' in df.columns:
            df['original_date'] = df['date'].copy()

        # Process the date column to standardize format
        if 'date' in df.columns:
            date_before_count = len(df)
            
            # Handle special case if dates are in numeric format (Excel dates)
            if pd.api.types.is_numeric_dtype(df['date']):
                try:
                    # Try to convert Excel numeric dates to datetime
                    df['date'] = pd.to_datetime(df['date'], unit='D', origin='1899-12-30', errors='coerce')
                    log_entries.append("Converted numeric Excel dates")
                except:
                    # If that fails, just coerce to datetime
                    df['date'] = pd.to_datetime(df['date'], errors='coerce')
            elif df['date'].dtype == object:  # String or mixed types
                # Handle different date formats by trying multiple approaches
                # First, check for common date formats in a sample
                
                # Try to infer from first few non-null values
                date_samples = []
                for idx, date_val in enumerate(df['date']):
                    if date_val is not None and str(date_val).strip() and len(date_samples) < 5:
                        date_samples.append(str(date_val).strip())
                    if len(date_samples) >= 5 or idx > 100:
                        break
                
                if date_samples:
                    # Try different date formats
                    date_formats = [
                        '%d/%m/%y', '%d/%m/%Y',  # European (day first)
                        '%m/%d/%y', '%m/%d/%Y',  # US (month first)
                        '%Y-%m-%d', '%Y/%m/%d',  # ISO
                        '%d-%m-%Y', '%d-%m-%y',  # European with dash
                        '%m-%d-%Y', '%m-%d-%y',  # US with dash
                        '%Y%m%d',                # Compact ISO
                        '%d.%m.%Y', '%d.%m.%y',  # European with dot
                    ]
                    
                    # Try each format with each sample to find the most likely one
                    format_success_count = {fmt: 0 for fmt in date_formats}
                    for sample in date_samples:
                        for fmt in date_formats:
                            try:
                                datetime.strptime(sample, fmt)
                                format_success_count[fmt] += 1
                            except:
                                continue
                    
                    # Find the format with the most successes
                    best_format = max(format_success_count.items(), key=lambda x: x[1])
                    if best_format[1] > 0:
                        detected_format = best_format[0]
                        if verbose:
                            print(f"Detected date format: {detected_format}")
                        log_entries.append(f"Detected date format: {detected_format}")
                        
                        # Apply the detected format
                        try:
                            df['date'] = pd.to_datetime(df['date'], format=detected_format, errors='coerce')
                        except:
                            # Fall back to pandas' auto-detection
                            df['date'] = pd.to_datetime(df['date'], errors='coerce')
                    else:
                        # No clear format detected, use pandas auto-detection
                        df['date'] = pd.to_datetime(df['date'], errors='coerce')
                else:
                    # No valid samples found, use default conversion
                    df['date'] = pd.to_datetime(df['date'], errors='coerce')
            else:
                # Already a datetime-like column
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
            
            # Check for NaT values in date column and report
            nat_count = df['date'].isna().sum()
            if nat_count > 0:
                if verbose:
                    print(f"Warning: {nat_count} dates could not be parsed")
                log_entries.append(f"Warning: {nat_count} dates could not be parsed")
        
        # --- NUMERIC COLUMN PROCESSING ---
        # Convert and clean OHLCV columns
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                # Store original values for debugging
                df[f'original_{col}'] = df[col].copy()
                
                # Special handling for columns with string/object data
                if df[col].dtype == object:
                    # Replace comma with dot for decimal points
                    df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
                    # Remove whitespace
                    df[col] = df[col].str.strip()
                    # Remove any currency symbols or other non-numeric characters
                    df[col] = df[col].str.replace(r'[^\d.-]', '', regex=True)
                
                # Convert to numeric, but maintain values that are very close to numeric
                # First try exact conversion
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
        # --- DATA CLEANUP ---
        # Make a copy for pre-cleanup comparison
        before_cleanup = df.copy()
        
        # Count NaN values per required column
        na_counts = {col: df[col].isna().sum() for col in required_columns if col in df.columns}
        for col, count in na_counts.items():
            if count > 0:
                log_entries.append(f"Column {col} has {count} missing values")
        
        # Check for major data issues
        if 'date' in df.columns and df['date'].isna().all():
            # All dates failed - try to restore from original
            if 'original_date' in df.columns:
                log_entries.append("All date conversions failed, attempting emergency recovery")
                # Try again with brute force approach
                df['date'] = pd.to_datetime(df['original_date'], errors='coerce')
                # If still all NaT, try creating a date range
                if df['date'].isna().all():
                    log_entries.append("Creating artificial date range as last resort")
                    df['date'] = pd.date_range(start='2000-01-01', periods=len(df), freq='D')
        
        # IMPORTANT: Check if we'd lose too much data
        na_data_percentage = df[required_columns].isna().any(axis=1).mean() if len(df) > 0 else 1.0
        if na_data_percentage > 0.95:  # Would lose more than 95% of data
            log_entries.append(f"WARNING: Would lose {na_data_percentage:.1%} of data - attempting recovery")
            
            # Try a row-by-row approach to salvage data
            valid_rows = []
            for idx, row in df.iterrows():
                # Check if we have at least date and close price
                if pd.notna(row.get('date')) and pd.notna(row.get('close')):
                    # Fill any missing values with estimates
                    if pd.isna(row.get('open')):
                        row['open'] = row['close']
                    if pd.isna(row.get('high')):
                        row['high'] = max(row['open'], row['close']) if pd.notna(row.get('open')) else row['close']
                    if pd.isna(row.get('low')):
                        row['low'] = min(row['open'], row['close']) if pd.notna(row.get('open')) else row['close']
                    if pd.isna(row.get('volume')):
                        row['volume'] = 0
                    valid_rows.append(row)
            
            if valid_rows:
                df = pd.DataFrame(valid_rows)
                log_entries.append(f"Recovered {len(df)} rows with at least date and close price")
            else:
                # Last ditch effort - check if there are any columns that could match OHLC
                log_entries.append("Emergency recovery failed, trying to extract data from raw dataframe")
                # Go back to the raw dataframe and try a different approach
                df = raw_df.copy()
                df.columns = [str(col).lower().strip() for col in df.columns]
                
                # Try to find date column
                date_candidates = [col for col in df.columns if any(kw in str(col).lower() for kw in ['date', 'time', 'day'])]
                if date_candidates:
                    df['date'] = pd.to_datetime(df[date_candidates[0]], errors='coerce')
                else:
                    # Create artificial date range
                    df['date'] = pd.date_range(start='2000-01-01', periods=len(df), freq='D')
                
                # Try to identify price columns based on numeric values
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                if len(numeric_cols) >= 4:
                    # Assume the first 4 numeric columns are OHLC
                    ohlc_cols = numeric_cols[:4]
                    df['open'] = df[ohlc_cols[0]]
                    df['high'] = df[ohlc_cols[1]].clip(lower=df[ohlc_cols[0]])
                    df['low'] = df[ohlc_cols[2]].clip(upper=df[ohlc_cols[0]])
                    df['close'] = df[ohlc_cols[3]]
                    df['volume'] = 0 if len(numeric_cols) < 5 else df[numeric_cols[4]]
                    log_entries.append(f"Created OHLCV data from numeric columns: {ohlc_cols}")
                else:
                    # Not enough numeric columns, assign defaults
                    for col in ['open', 'high', 'low', 'close']:
                        if col not in df.columns:
                            df[col] = 100.0  # Default price
                    if 'volume' not in df.columns:
                        df['volume'] = 0
                    log_entries.append("Created default OHLCV data as last resort")
        
        # Sort by date
        if 'date' in df.columns:
            df = df.sort_values('date')
        
        # Check for duplicate dates
        if 'date' in df.columns:
            duplicate_dates = df.duplicated(subset=['date']).sum()
            if duplicate_dates > 0:
                if verbose:
                    print(f"Warning: Found {duplicate_dates} duplicate dates. Keeping the last occurrence.")
                log_entries.append(f"Warning: Found {duplicate_dates} duplicate dates. Keeping the last occurrence.")
                df = df.drop_duplicates(subset=['date'], keep='last')
        
        # --- ADD CALCULATED COLUMNS ---
        # Add calculated columns if we have the required data
        if all(col in df.columns for col in ['high', 'low', 'close']):
            df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
        
        if 'adj_close' in df.columns and 'close' in df.columns:
            # Avoid division by zero
            df['adj_factor'] = np.where(df['close'] > 0, df['adj_close'] / df['close'], 1.0)
            # Create adjusted OHLC columns
            for col in ['open', 'high', 'low']:
                if col in df.columns:
                    df[f'adj_{col}'] = df[col] * df['adj_factor']
        
        # Extract ticker from filename if possible
        try:
            # Try to get ticker from filename, assuming format like "AAPL_daily.csv"
            ticker = file_base.split("_")[0].upper()
            if ticker and len(ticker) <= 6:  # Reasonable ticker length
                df['ticker'] = ticker
                if verbose:
                    print(f"Added ticker column: {ticker}")
                log_entries.append(f"Added ticker column: {ticker}")
        except:
            if verbose:
                print("Could not extract ticker from filename")
            log_entries.append("Could not extract ticker from filename")
        
        # --- FINAL CLEANUP ---
        # Essential data checks - make sure data is reasonable
        # Ensure high >= low
        if 'high' in df.columns and 'low' in df.columns:
            invalid_hl = (df['high'] < df['low']).sum()
            if invalid_hl > 0:
                log_entries.append(f"Fixed {invalid_hl} rows where high < low")
                # Fix by swapping high and low where needed
                mask = df['high'] < df['low']
                df.loc[mask, ['high', 'low']] = df.loc[mask, ['low', 'high']].values
        
        # Ensure open and close are between high and low
        if all(col in df.columns for col in ['open', 'high', 'low', 'close']):
            # Fix open outside range
            open_too_high = (df['open'] > df['high']).sum()
            if open_too_high > 0:
                log_entries.append(f"Fixed {open_too_high} rows where open > high")
                df.loc[df['open'] > df['high'], 'open'] = df.loc[df['open'] > df['high'], 'high']
            
            open_too_low = (df['open'] < df['low']).sum()
            if open_too_low > 0:
                log_entries.append(f"Fixed {open_too_low} rows where open < low")
                df.loc[df['open'] < df['low'], 'open'] = df.loc[df['open'] < df['low'], 'low']
            
            # Fix close outside range
            close_too_high = (df['close'] > df['high']).sum()
            if close_too_high > 0:
                log_entries.append(f"Fixed {close_too_high} rows where close > high")
                df.loc[df['close'] > df['high'], 'close'] = df.loc[df['close'] > df['high'], 'high']
            
            close_too_low = (df['close'] < df['low']).sum()
            if close_too_low > 0:
                log_entries.append(f"Fixed {close_too_low} rows where close < low")
                df.loc[df['close'] < df['low'], 'close'] = df.loc[df['close'] < df['low'], 'low']
        
        # Define columns to keep
        columns_to_keep = ['date', 'open', 'high', 'low', 'close', 'volume']
        
        # Add optional columns if they exist
        for col in ['typical_price', 'adj_close', 'adj_open', 'adj_high', 'adj_low', 'vwap', 'ticker']:
            if col in df.columns:
                columns_to_keep.append(col)
        
        # Save debug data with original values
        debug_columns = columns_to_keep.copy()
        original_columns = [c for c in df.columns if c.startswith('original_')]
        debug_columns.extend(original_columns)
        debug_df = df[debug_columns].copy()
        debug_path = os.path.join(output_dir, f"{file_base}_debug.csv")
        debug_df.to_csv(debug_path, index=False)
        
        # Keep only the required columns for the final output
        df = df[columns_to_keep]
        
        # Convert date to string in ISO format (YYYY-MM-DD)
        if 'date' in df.columns and pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = df['date'].dt.strftime('%Y-%m-%d')
        
        # --- FINAL REPORTING AND SAVE ---
        final_row_count = len(df)
        data_retention = (final_row_count / original_row_count) * 100 if original_row_count > 0 else 0
        
        log_entries.append(f"Original row count: {original_row_count}")
        log_entries.append(f"Final row count: {final_row_count}")
        log_entries.append(f"Data retention: {data_retention:.2f}%")
        
        if data_retention < 50:
            log_entries.append("WARNING: Significant data loss occurred during processing")
            if verbose:
                print(f"WARNING: Only {data_retention:.2f}% of original data was retained")
        
        # Save to CSV in a standardized format
        df.to_csv(output_file, index=False)
        if verbose:
            print(f"Arranged data saved to {output_file}")
            print(f"Retained {final_row_count} of {original_row_count} rows ({data_retention:.2f}%)")
        
        # Create log file
        log_path = os.path.join(output_dir, f"{file_base}_log.txt")
        with open(log_path, 'w') as log:
            log.write(f"Data Arrangement Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            log.write("="*50 + "\n\n")
            for entry in log_entries:
                log.write(f"{entry}\n")
            log.write("\n" + "="*50 + "\n")
            log.write(f"Final shape: {df.shape}\n")
            log.write(f"Final columns: {list(df.columns)}\n")
            if len(df) > 0:
                if 'date' in df.columns:
                    log.write(f"Date range: {df['date'].min()} to {df['date'].max()}\n")
                if all(col in df.columns for col in ['low', 'high']):
                    log.write(f"Price range: {df['low'].min():.2f} to {df['high'].max():.2f}\n")
        
        # Also save a preview file in Excel format for easier inspection
        if len(df) > 0:
            preview_path = os.path.join(output_dir, f"{file_base}_preview.xlsx")
            preview_df = df.head(100)
            preview_df.to_excel(preview_path, index=False)
            if verbose:
                print(f"Preview file saved to {preview_path}")
        
        return output_file
        
    except Exception as e:
        error_msg = f"Error arranging file: {str(e)}"
        if verbose:
            print(error_msg)
            traceback.print_exc()
        
        # Create error log
        log_path = os.path.join(output_dir, f"{file_base}_error_log.txt")
        with open(log_path, 'w') as log:
            log.write(f"Error Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            log.write("="*50 + "\n\n")
            for entry in log_entries:
                log.write(f"{entry}\n")
            log.write("\n" + "="*50 + "\n")
            log.write(f"ERROR: {str(e)}\n\n")
            log.write(traceback.format_exc())
        
        raise

# For direct testing
if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 else "data"
        arrange_data_file(input_file, output_dir)
    else:
        print("Please provide a file path as an argument.")
        print("Usage: python data_arranger_script.py <input_file_path> [output_directory]") 