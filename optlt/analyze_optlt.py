import pandas as pd
import numpy as np

# Create a Python script to analyze the Excel file
def analyze_excel_file(file_path):
    try:
        # Try reading with xlrd (for older .xls files)
        excel_data = pd.read_excel(file_path, sheet_name=None, engine='xlrd')
        print("Successfully read the file using xlrd engine")
    except Exception as e:
        print(f"Error with xlrd: {e}")
        try:
            # Try with openpyxl (for newer .xlsx files)
            excel_data = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')
            print("Successfully read the file using openpyxl engine")
        except Exception as e:
            print(f"Error with openpyxl: {e}")
            return None
    
    # Print available sheets
    print("\nAvailable sheets:", list(excel_data.keys()))
    
    # Analyze each sheet
    for sheet_name, df in excel_data.items():
        print(f"\n{'='*50}")
        print(f"Sheet: {sheet_name}")
        print(f"{'='*50}")
        
        # Print basic info
        print(f"\nShape: {df.shape}")
        print("\nColumn names:")
        for col in df.columns:
            print(f"  - {col}")
        
        # Print first few rows
        print("\nFirst 10 rows:")
        print(df.head(10))
        
        # Check for formulas or calculations
        print("\nChecking for potential formula columns...")
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if len(df[col].dropna()) > 0:
                print(f"  - {col}: Range [{df[col].min()} to {df[col].max()}]")
    
    return excel_data

if __name__ == "__main__":
    file_path = "/home/ubuntu/upload/optlt.xls"
    analyze_excel_file(file_path)
