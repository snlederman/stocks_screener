import pandas as pd
from software.data_manager import fetch_data
from software.analysis_tools import prepare_and_forecast_model
from stock_screener import setup_overview, filters_dict
from portfolio_manager import optimize_portfolio, rebalance_portfolio
from software.daily_operations import load_existing_portfolio, save_portfolio, update_portfolio
import datetime
import logging

STEP = 90
SLOPES_END_POINT = 360*1 #Days in a year by years
EMA_SPAN = 10 #alpha = 2/(span+1)
AVERAGE_SLOPE_THRESHOLD = 0.5
RISK_ADJUSTED_SLOPE_THRESHOLD = 10
CAPITAL = 1000

# Configure logging
logging.basicConfig(filename='../trading_log.log', level=logging.INFO,
                    format='%(asctime)s %(message)s')

def log_decisions(date, transactions, portfolio):
    """Logs the algorithm's decisions for a particular date."""
    logging.info(f"Date: {date}")
    logging.info(f"Transactions: {transactions}")
    logging.info(f"Portfolio: {portfolio}")


def backtest(start_date, end_date):
    """Backtest the trading strategy between two dates."""
    current_date = start_date

    daily_returns = []
    existing_portfolio = load_existing_portfolio()

    while current_date <= end_date:
        overview = setup_overview(filters_dict)
        pd_data = overview.screener_view()  # returns a DataFrame with tickers
        significant_stocks = []
        stock_data = {}
        for index, row in pd_data.iterrows():
            ticker = row['Ticker']
            data = fetch_data(ticker)
            if not data.empty:
                slopes = prepare_and_forecast_model(data, list(range(STEP, SLOPES_END_POINT + 1, STEP)))
                if slopes:
                    ema = pd.Series(slopes[::-1]).ewm(span=EMA_SPAN).mean().iloc[-1]
                    emv = pd.Series(slopes[::-1]).ewm(span=EMA_SPAN).var().iloc[-1]
                    risk_adjusted_slope = ema / emv if emv != 0 else 0
                    if ema > AVERAGE_SLOPE_THRESHOLD and risk_adjusted_slope > RISK_ADJUSTED_SLOPE_THRESHOLD:
                        significant_stocks.append(ticker)
                        stock_data[ticker] = data['close']

        if significant_stocks:
            prices = pd.DataFrame(stock_data)
            weights = optimize_portfolio(prices)
            transactions = rebalance_portfolio(existing_portfolio, weights)
            existing_portfolio = update_portfolio(existing_portfolio, transactions, prices)
            save_portfolio(existing_portfolio)
            log_decisions(current_date, transactions, existing_portfolio)

        daily_returns.append(existing_portfolio['daily_return'].iloc[-1])
        current_date += pd.DateOffset(days=1)

    return daily_returns

if __name__ == "__main__":
    start_date = pd.Timestamp('2020-01-01')
    end_date = pd.Timestamp(datetime.datetime.today().strftime('%Y-%m-%d'))
    daily_returns = backtest(start_date, end_date)
    print(daily_returns)
