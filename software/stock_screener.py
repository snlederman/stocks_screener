import time
import requests
from yahoo_fin import stock_info as si
import pyarrow as pa
import pyarrow.parquet as pq
from tqdm import tqdm
import pandas as pd
from datetime import datetime,timedelta

api_key = "fb9af3b1d45dda27119a970ab5f5a92c"

def fetch_statement(ticker):
    url = f"https://financialmodelingprep.com/api/v3/historical/earning_calendar/{ticker}?apikey={api_key}"
    #url = f"https://financialmodelingprep.com/api/v3/income-statement/{ticker}?period=quarter&apikey={api_key}"
    try:
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            try:
                for entry in response.json():
                    entry['date'] = datetime.strptime(entry['date'], '%Y-%m-%d')
                    fixed_date = datetime.strptime('1987-01-01', '%Y-%m-%d')


            except ValueError as e:
                print(f"JSON parsing error for {ticker}: {e}")
                return None
            return [{
                'ticker': statement['symbol'],
                'date': statement['date'],
                'eps': statement['eps'],
                'revenue': statement['revenue']
            } for statement in income_statements]
        elif response.status_code == 429:
            print("Hit rate limit, sleeping for 60 seconds")
            time.sleep(60)  # Sleep for a minute when rate limit is hit
            return fetch_statement(ticker)  # Retry the request
        else:
            print(f"Failed to fetch data for {ticker} with status {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request failed for {ticker} with exception {e}")
        return None

stocks = list(set(si.tickers_dow() + si.tickers_nasdaq() + si.tickers_other()))
schema = pa.schema([
    ('ticker', pa.string()),
    ('date', pa.string()),
    ('eps', pa.float64()),
    ('revenue', pa.float64()),
])

writer = pq.ParquetWriter('income_statements.parquet', schema)

try:
    for ticker in tqdm(stocks, desc="Processing stocks"):
        records = fetch_statement(ticker)
        if records:
            for record in records:
                table = pa.Table.from_pandas(pd.DataFrame([record]), schema=schema)
                writer.write_table(table)
finally:
    writer.close()
