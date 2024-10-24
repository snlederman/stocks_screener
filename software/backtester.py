import pandas as pd
import matplotlib.pyplot as plt


def backtest_strategy(signals, prices, initial_capital=10000):
    """
    Execute trades based on strategy signals and calculate portfolio value over time.

    :param signals: DataFrame with signals ('buy' or 'sell') for each stock and date
    :param prices: DataFrame with stock prices
    :param initial_capital: float, initial amount of money available to trade
    :return: DataFrame with portfolio values over time
    """
    cash = initial_capital
    positions = pd.DataFrame(index=signals.index, columns=signals.columns).fillna(0)
    portfolio = pd.DataFrame(index=signals.index, columns=['cash', 'holdings', 'total']).fillna(0)

    for date in signals.index:
        # Handle buying/selling based on the signals
        signals_date = signals.loc[date]
        prices_date = prices.loc[date]

        # Sell any stocks where signal is 'sell'
        for stock in positions.columns:
            if signals_date[stock] == 'sell' and positions.at[date, stock] > 0:
                cash += positions.at[date, stock] * prices_date[stock]
                positions.at[date, stock] = 0

        # Buy stocks where signal is 'buy'
        buy_stocks = signals_date[signals_date == 'buy'].index.tolist()
        if buy_stocks:
            buy_budget_per_stock = cash / len(buy_stocks)
            for stock in buy_stocks:
                positions.at[date, stock] += buy_budget_per_stock / prices_date[stock]
                cash -= buy_budget_per_stock

        # Update portfolio values
        portfolio.at[date, 'cash'] = cash
        portfolio.at[date, 'holdings'] = (positions.loc[date] * prices_date).sum()
        portfolio.at[date, 'total'] = portfolio.at[date, 'cash'] + portfolio.at[date, 'holdings']

    return portfolio


def plot_results(portfolio):
    """Plot the backtesting results of the portfolio over time."""
    plt.figure(figsize=(12, 6))
    portfolio['total'].plot(title='Portfolio Value Over Time')
    plt.xlabel('Date')
    plt.ylabel('Total Portfolio Value')
    plt.show()