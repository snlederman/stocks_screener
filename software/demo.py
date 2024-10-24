import logging
import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend
import matplotlib.pyplot as plt
import os
import requests
import re
from datetime import datetime, date
import xml.etree.ElementTree as ET
from lxml import html
from ib_insync import *
from yahoo_fin.stock_info import get_data
import pandas as pd
import pandas_ta as ta

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to fetch and parse fundamental data from Interactive Brokers
def fetch_fundamental_data(ticker):
    # Set up the connection parameters
    host = os.getenv('IB_HOST', 'host.docker.internal')
    port = int(os.getenv('IB_PORT', '4001'))
    ib = IB()
    ib.connect(host, port, clientId=1)

    contract = Stock(ticker, 'SMART', 'USD')
    fundamental_data = ib.reqFundamentalData(contract, 'ReportsFinSummary')
    estimates_data = ib.reqFundamentalData(contract, 'RESC')

    root = ET.fromstring(fundamental_data)
    rootx = ET.fromstring(estimates_data)

    ib.disconnect()
    return root, rootx


# Function to extract EPS values
def extract_eps_values(rootx, year, value_type='ActValue'):
    if value_type == 'ActValue':
        for elem in rootx.findall('.//FYActual[@type="EPS"]//FYPeriod'):
            if elem.get('fYear') == str(year) and elem.get('periodType') == 'A':
                value_elem = elem.find('.//ActValue')
                if value_elem is not None:
                    return float(value_elem.text)
    elif value_type == 'ConsValue':
        for elem in rootx.findall('.//FYEstimate[@type="EPS"]//FYPeriod'):
            if elem.get('fYear') == str(year) and elem.get('periodType') == 'A':
                value_elem = elem.find('.//ConsEstimate[@type="Mean"]//ConsValue[@dateType="CURR"]')
                if value_elem is not None:
                    return float(value_elem.text)
    return None


# Function to fetch stock price data
def fetch_stock_data(ticker):
    try:
        data = get_data(ticker)
        if 'close' not in data.columns:
            return pd.DataFrame()
        return data[['close']]
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return pd.DataFrame()


# Function to calculate technical indicators
def calculate_indicators(data):
    data['SMA_20'] = data['close'].rolling(window=20).mean()
    data['SMA_50'] = data['close'].rolling(window=50).mean()
    data['SMA_200'] = data['close'].rolling(window=200).mean()
    data['RSI_14'] = ta.rsi(data['close'], length=14)
    return data


# Function to apply filters
def apply_filters(ticker, current_date):
    data = fetch_stock_data(ticker)
    if data.empty:
        return None

    current_datetime = pd.to_datetime(current_date)
    data = data[data.index <= current_datetime]  # Filter data up to the given date
    if data.empty:
        return None

    data = calculate_indicators(data)
    latest_close = data['close'].iloc[-1]
    sma20 = data['SMA_20'].iloc[-1]
    sma50 = data['SMA_50'].iloc[-1]
    sma200 = data['SMA_200'].iloc[-1]
    rsi14 = data['RSI_14'].iloc[-1]

    if latest_close <= 10:
        return None
    if rsi14 < 60:
        return None
    if latest_close < sma20 or latest_close < sma50 or latest_close < sma200:
        return None

    root, rootx = fetch_fundamental_data(ticker)

    eps_actual_current_year = extract_eps_values(rootx, current_date.year, value_type='ActValue')
    eps_estimate_next_year = extract_eps_values(rootx, current_date.year + 1, value_type='ConsValue')
    eps_estimate_year_after_next = extract_eps_values(rootx, current_date.year + 2, value_type='ConsValue')

    if eps_actual_current_year and eps_estimate_next_year:
        eps_growth_this_year = (eps_estimate_next_year - eps_actual_current_year) / abs(eps_actual_current_year) * 100
        if eps_growth_this_year <= 20:
            return None

    if eps_estimate_next_year and eps_estimate_year_after_next:
        eps_growth_next_year = (eps_estimate_year_after_next - eps_estimate_next_year) / abs(
            eps_estimate_next_year) * 100
        if eps_growth_next_year <= 20:
            return None

    # Add more filters as necessary
    return ticker


import backtrader as bt

class ReturnAnalyzer(bt.Analyzer):
    def __init__(self):
        self.rets = []

    def next(self):
        self.rets.append(self.strategy.broker.getvalue())

    def get_analysis(self):
        daily_rets = pd.Series(self.rets).pct_change().dropna()
        final_return = (self.rets[-1] / self.rets[0]) - 1 if len(self.rets) > 0 else 0
        return {
            'daily_returns': daily_rets,
            'final_return': final_return
        }

class ScreenerStrategy(bt.Strategy):
    params = (
        ('ema_span', 20),
        ('risk_adjusted_slope_threshold', 0.5),
        ('profit_target', 0.20),
        ('max_positions', 10),  # Max number of positions in the portfolio
    )

    def __init__(self):
        self.order = None
        self.buy_price = {}
        self.dataclose = {d: d.close for d in self.datas}
        self.sma50 = {d: bt.indicators.SimpleMovingAverage(d.close, period=50) for d in self.datas}
        self.tickers = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN']
        self.selected_stocks = set()

    def next(self):
        current_date = self.datas[0].datetime.date(0)
        self.selected_stocks.clear()

        # Daily screening
        for ticker in self.tickers:
            selected_ticker = apply_filters(ticker, current_date)
            if selected_ticker:
                self.selected_stocks.add(selected_ticker)

        # Check portfolio space
        current_positions = len(self.broker.positions)

        for data in self.datas:
            if self.order:
                continue

            position = self.getposition(data)
            if not position and data._name in self.selected_stocks and current_positions < self.params.max_positions:
                # Perform risk-adjusted slope calculation outside of Backtrader
                df = fetch_stock_data(data._name)
                df = calculate_indicators(df)
                slopes = df['close'].diff().dropna()
                ema = slopes.ewm(span=self.params.ema_span).mean().iloc[-1]
                emv = slopes.ewm(span=self.params.ema_span).var().iloc[-1]
                risk_adjusted_slope = ema / emv if emv != 0 else 0

                if risk_adjusted_slope > self.params.risk_adjusted_slope_threshold:
                    self.buy_price[data] = self.dataclose[data][0]
                    self.order = self.buy(data=data)
                    current_positions += 1
                    logger.info(f"Buy order placed for {data._name} at {self.dataclose[data][0]}")
            elif position:
                # Sell criteria
                if self.dataclose[data][0] >= self.buy_price[data] * (1 + self.params.profit_target):
                    self.order = self.sell(data=data)
                    logger.info(f"Sell order placed for {data._name} at {self.dataclose[data][0]}")
                elif self.dataclose[data][0] < self.sma50[data][0]:
                    self.order = self.sell(data=data)
                    logger.info(f"Sell order placed for {data._name} at {self.dataclose[data][0]}")


# Prepare the historical data
tickers = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'AMZN']
start_date = '2023-01-01'
end_date = '2024-01-01'

# Run the strategy
cerebro = bt.Cerebro()
for ticker in tickers:
    data = fetch_stock_data(ticker)
    data = data[(data.index >= start_date) & (data.index <= end_date)]
    if not data.empty:
        data = bt.feeds.PandasData(dataname=data)
        cerebro.adddata(data, name=ticker)

cerebro.addstrategy(ScreenerStrategy)
cerebro.addanalyzer(ReturnAnalyzer, _name='return_analyzer')
cerebro.broker.set_cash(100000)
cerebro.broker.setcommission(commission=0.001)

results = cerebro.run()

# Extract the analysis
analysis = results[0].analyzers.return_analyzer.get_analysis()
daily_returns = analysis['daily_returns']
final_return = analysis['final_return']

# Save daily returns to a CSV file
daily_returns.to_csv('daily_returns.csv')

# Print final return
print(f"Final Return: {final_return * 100:.2f}%")
