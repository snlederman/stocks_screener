from yahoo_fin.stock_info import get_data
import pandas as pd
import pandas_ta as ta

def fetch_data(ticker):
    """Fetches historical closing prices for a given stock, ensuring the 'close' column is present and the DataFrame is consistent."""
    try:
        data = get_data(ticker)
        if 'close' not in data.columns:
            print(f"'close' column missing in data for {ticker}.")
            return pd.DataFrame()  # Return empty DataFrame with consistent index
        return data[[PRICE_STRATEGY]]  # Ensure only 'close' column is returned
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return pd.DataFrame()  # Return empty DataFrame with consistent index

df = fetch_data('NVDA')

# Calculate the moving averages
df['SMA_20'] = df['close'].rolling(window=20).mean()
df['SMA_50'] = df['close'].rolling(window=50).mean()
df['SMA_200'] = df['close'].rolling(window=200).mean()

# Calculate the RSI with a period of 14
df['RSI_14'] = ta.rsi(df['close'], length=14)

# Display the first few rows of the DataFrame
print(df)  # Adjust the number to see more rows if needed