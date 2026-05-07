import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
sheet_id = os.getenv('GOOGLE_SHEETS_ID')
csv_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0'

try:
    df = pd.read_csv(csv_url)
    print("Columns:", df.columns.tolist())
    print("\nFirst 5 rows:")
    print(df.head())
except Exception as e:
    print(f"Error: {e}")
