from pypfopt import EfficientFrontier, risk_models, expected_returns
from collections import defaultdict

def optimize_portfolio(prices):
    """ Optimize the portfolio to find the maximum Sharpe ratio. """
    mu = expected_returns.mean_historical_return(prices)
    cov_matrix = risk_models.sample_cov(prices)
    ef = EfficientFrontier(mu, cov_matrix)
    ef.max_sharpe()
    cleaned_weights = ef.clean_weights()
    return cleaned_weights


def rebalance_portfolio(current_portfolio, target_weights):
    transactions = defaultdict(float)
    total_value = current_portfolio['total_value'].sum()
    current_weights = current_portfolio.set_index('ticker')['total_value'] / total_value

    # Identify stocks to be sold entirely or partially
    for ticker, current_weight in current_weights.items():
        target_weight = target_weights.get(ticker, 0)
        if target_weight < current_weight:
            current_value = current_portfolio[current_portfolio['ticker'] == ticker]['total_value'].sum()
            target_value = target_weight * total_value
            adjustment = target_value - current_value
            transactions[ticker] += adjustment

    # Identify stocks to be bought or added
    for ticker, target_weight in target_weights.items():
        current_weight = current_weights.get(ticker, 0)
        if target_weight > current_weight:
            current_value = current_portfolio[current_portfolio['ticker'] == ticker]['total_value'].sum()
            target_value = target_weight * total_value
            adjustment = target_value - current_value
            transactions[ticker] += adjustment

    return dict(transactions)

