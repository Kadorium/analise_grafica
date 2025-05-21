import pandas as pd

# Check the Excel file
file_path = 'data/test multidata.xlsx'
print(f"Checking file: {file_path}")

try:
    excel_file = pd.ExcelFile(file_path)
    sheet_names = excel_file.sheet_names
    print(f"Sheets found: {sheet_names}")
    
    # Check a sample from the first sheet
    first_sheet = sheet_names[0]
    df = pd.read_excel(excel_file, sheet_name=first_sheet)
    print(f"\nColumns in {first_sheet}:")
    print(df.columns.tolist())
    
    print("\nSample data:")
    print(df.head(2))
    
except Exception as e:
    print(f"Error: {str(e)}") 