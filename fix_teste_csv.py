import pandas as pd
import os
import datetime
import json

def fix_teste_csv():
    """Fix the specific teste.csv file with European format."""
    input_file = "data/teste.csv"
    output_file = "data/teste_fixed.csv"
    
    print(f"Fixing file: {input_file}")
    
    # Load the file with European format settings
    df = pd.read_csv(
        input_file, 
        sep=';', 
        decimal=',',
        encoding='utf-8',
        encoding_errors='replace',
        on_bad_lines='skip'
    )
    
    print(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
    print("\nOriginal data sample:")
    print(df.head())
    
    # Fix date format (convert DD/MM/YY to datetime)
    print("\nFixing dates...")
    
    # Custom function to handle various date formats
    def parse_date(date_str):
        if not isinstance(date_str, str):
            return None
            
        date_str = date_str.strip()
        
        # Try different formats
        formats = ['%d/%m/%y', '%d/%m/%Y', '%m/%d/%y', '%m/%d/%Y']
        
        for fmt in formats:
            try:
                return pd.to_datetime(date_str, format=fmt)
            except:
                continue
                
        # If all formats fail, try pandas' flexible parser
        try:
            return pd.to_datetime(date_str, errors='coerce')
        except:
            return None
    
    # Apply the date parser
    df['date'] = df['date'].apply(parse_date)
    
    # Convert numeric columns (replace comma with dot for decimal)
    num_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in num_cols:
        if col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].astype(str).str.replace(',', '.')
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Remove empty columns
    for col in df.columns:
        if 'unnamed' in col.lower():
            if df[col].isna().all():
                df = df.drop(columns=[col])
    
    # Drop rows with missing values
    before_rows = len(df)
    df = df.dropna()
    after_rows = len(df)
    
    print(f"Removed {before_rows - after_rows} rows with missing values")
    print(f"Final dataset: {len(df)} rows")
    
    # Print sample of fixed data
    print("\nFixed data sample:")
    print(df.head())
    
    # Save to CSV
    df.to_csv(output_file, index=False)
    print(f"\nSaved fixed data to {output_file}")
    
    # Also save a pickle file for faster loading
    pickle_file = output_file.replace('.csv', '.pkl')
    df.to_pickle(pickle_file)
    print(f"Saved pickle file to {pickle_file}")
    
    # Test JSON conversion
    json_data = df.head().to_json(orient='records')
    print("\nJSON sample:")
    print(json_data[:200] + "..." if len(json_data) > 200 else json_data)
    
    return df

if __name__ == "__main__":
    fixed_data = fix_teste_csv() 