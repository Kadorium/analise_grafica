import os
import sys
import json
import pandas as pd
import datetime
from data.data_loader import DataLoader

def test_file(file_path):
    """Test loading and processing a CSV file with our DataLoader."""
    print(f"Testing file: {file_path}")
    print("-" * 50)
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    print(f"File size: {os.path.getsize(file_path)} bytes")
    
    # Try to read the first few lines to diagnose structure
    print("\nFile preview (first 5 lines):")
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            for i, line in enumerate(f):
                if i < 5:
                    print(f"Line {i+1}: {line.strip()}")
                else:
                    break
    except Exception as e:
        print(f"Error reading file preview: {str(e)}")
    
    # Try loading with DataLoader
    print("\nTrying to load with DataLoader:")
    try:
        loader = DataLoader(file_path)
        data = loader.load_csv()
        print(f"Success! Loaded {len(data)} rows and {len(data.columns)} columns")
        print(f"Columns: {list(data.columns)}")
        print("\nSample data:")
        print(data.head())
        
        # Fix the date column manually for testing
        print("\nTrying to manually fix dates:")
        data_copy = data.copy()
        
        # Debug the date format
        date_examples = data_copy['date'].head(3).tolist()
        print(f"Date examples: {date_examples}")
        
        # Try the European DD/MM/YY format directly
        try:
            # For years represented as '13' meaning 2013
            data_copy['date_fixed'] = data_copy['date'].apply(
                lambda x: datetime.datetime.strptime(x, '%d/%m/%y').date() if isinstance(x, str) else None
            )
            print("European DD/MM/YY format looks correct!")
            print(data_copy[['date', 'date_fixed']].head())
            
            # Update the data with fixed dates
            data_copy['date'] = data_copy['date_fixed']
            data_copy = data_copy.drop(columns=['date_fixed'])
            
            # Now clean the data with numbers fixed
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in data_copy.columns:
                    # Replace comma with dot for decimal points
                    if data_copy[col].dtype == object:
                        data_copy[col] = data_copy[col].astype(str).str.replace(',', '.')
                    data_copy[col] = pd.to_numeric(data_copy[col], errors='coerce')
            
            # Drop unnamed columns
            for col in data_copy.columns:
                if 'unnamed' in col.lower():
                    if data_copy[col].isna().all():
                        data_copy = data_copy.drop(columns=[col])
            
            # Check if we have valid data now
            print(f"\nFixed data with {len(data_copy)} rows")
            print(data_copy.head())
            
            # Try converting to JSON
            print("\nTrying to convert fixed data to JSON:")
            json_data = data_copy.head().to_json(orient='records')
            parsed_json = json.loads(json_data)
            print(f"Success! Valid JSON with {len(parsed_json)} records")
            print(json_data[:200] + "..." if len(json_data) > 200 else json_data)
            
            # Save the fixed data to a clean CSV
            fixed_file = file_path.replace('.csv', '_fixed.csv')
            data_copy.to_csv(fixed_file, index=False)
            print(f"\nSaved fixed data to {fixed_file}")
            
            return data_copy
            
        except Exception as e:
            print(f"Error fixing dates: {str(e)}")
        
        # Try cleaning the data with the standard process
        print("\nTrying standard clean_data process:")
        cleaned_data = loader.clean_data()
        print(f"Success! Cleaned data has {len(cleaned_data)} rows")
        print("\nCleaned sample data:")
        print(cleaned_data.head())
        
        # Try converting to JSON
        print("\nTrying to convert to JSON:")
        json_data = cleaned_data.head().to_json(orient='records')
        parsed_json = json.loads(json_data)  # Will fail if JSON is invalid
        print(f"Success! Valid JSON with {len(parsed_json)} records")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Test the provided file
    test_file("data/teste.csv") 