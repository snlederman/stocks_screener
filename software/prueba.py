import pandas as pd
from datetime import datetime, timedelta
import time
import requests
from yahoo_fin import stock_info as si
import pyarrow as pa
import pyarrow.parquet as pq
from tqdm import tqdm
import pandas as pd

api_key = "fb9af3b1d45dda27119a970ab5f5a92c"

stocks = list(set(si.tickers_dow() + si.tickers_nasdaq() + si.tickers_other()))
stocks.sort()
print(len(stocks))
i = 6
print(stocks[i])
url = f"https://financialmodelingprep.com/api/v3/historical/earning_calendar/{stocks[i]}?apikey={api_key}"
response = requests.get(url, timeout=20)
data = response.json()
print(data)
# Convert the 'date' string to a datetime object for easier comparison
for entry in data:
    entry['date'] = datetime.strptime(entry['date'], '%Y-%m-%d')

# Fixed date to compare to
fixed_date = datetime.strptime('2023-05-08', '%Y-%m-%d')

# Sort data by date
data.sort(key=lambda x: x['date'])

# Function to find the closest past date and other required data
def find_relevant_data(data, fixed_date):
    past_dates = [d for d in data if d['date'] <= fixed_date]
    if not past_dates:
        closest_past = None
    else:
        closest_past = max(past_dates, key=lambda x: x['date'])

    try:
        # Find the next available entry after the closest past date
        next_index = data.index(closest_past) - 1
        next_available = data[next_index]
    except (IndexError, ValueError):
        next_available = None

    # Find the entry that is about one year later from the closest past date
    if closest_past:
        one_year_earlier = closest_past['date'] + timedelta(days=-365)
        older_dates = [d for d in data if d['date'] >= one_year_earlier]
        if not older_dates:
            past_year = None
        else:
            past_year = min(older_dates, key=lambda x: abs(x['date'] - one_year_earlier))
    else:
       past_year = None

    # Find the entry that is about one year later from the closest past date
    if closest_past:
        one_year_later = closest_past['date'] + timedelta(days=365)
        future_dates = [d for d in data if d['date'] >= one_year_later]
        if not future_dates:
            next_year = None
        else:
            next_year = min(future_dates, key=lambda x: abs(x['date'] - one_year_later))
    else:
        next_year = None

    return closest_past, next_available, past_year, next_year

closest_past_data, next_available_data, past_year_data, next_year_data = find_relevant_data(data, fixed_date)

# Print the results
print("Closest Past Date Data:", closest_past_data)
print("Next Available Date Data:", next_available_data)
print("Past Year Date Data:", past_year_data)
print("Next Year Date Data:", next_year_data)
