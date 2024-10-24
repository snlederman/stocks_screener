from yahoo_fin import stock_info as si

# Function to get all US stock tickers
def get_all_us_stock_tickers():
    us_tickers = set()
    us_tickers.update(si.tickers_dow())
    us_tickers.update(si.tickers_nasdaq())
    us_tickers.update(si.tickers_sp500())
    us_tickers.update(si.tickers_other())
    return sorted(us_tickers)

print(get_all_us_stock_tickers())