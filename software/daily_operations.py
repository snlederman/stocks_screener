import pandas as pd

INITIAL_CAPITAL = 1000

def load_existing_portfolio(filepath="portfolio.json"):
    try:
        portfolio = pd.read_json(filepath)
        return portfolio
    except FileNotFoundError:
        # Initialize with starting capital if file doesn't exist
        return pd.DataFrame({
            'ticker': ['Cash'],
            'shares': [INITIAL_CAPITAL],
            'price': [1],
            'total_value': [INITIAL_CAPITAL]
        })


def save_portfolio(portfolio, filepath="portfolio.json"):
    """Save the current state of the portfolio to a JSON file."""
    portfolio.to_json(filepath)


def update_portfolio(existing_portfolio, transactions, prices):
    total_spent = 0

    # Process each transaction
    for ticker, transaction_amount in transactions.items():
        if ticker in list(existing_portfolio['ticker']):
            # Update existing positions
            if ticker != 'Cash' and prices[ticker].iloc[-1] != 0:  # Ensure no division by zero
                row_index = existing_portfolio.loc[existing_portfolio['ticker'] == ticker].index[0]
                new_shares = (existing_portfolio.at[row_index, 'total_value'] + transaction_amount) / prices[ticker].iloc[-1]
                existing_portfolio.at[row_index, 'shares'] = new_shares
                existing_portfolio.at[row_index, 'price'] = prices[ticker].iloc[-1]
                existing_portfolio.at[row_index, 'total_value'] = new_shares * prices[ticker].iloc[-1]
        else:
            # Add new positions
            if ticker != 'Cash' and prices[ticker].iloc[-1] != 0:  # Ensure no division by zero
                new_shares = transaction_amount / prices[ticker].iloc[-1]
                existing_portfolio.loc[len(existing_portfolio)] = {'ticker': ticker, 'shares': new_shares, 'price': prices[ticker].iloc[-1], 'total_value': new_shares * prices[ticker].iloc[-1]}

        # Accumulate the total spent on purchases (positive transactions)
        if transaction_amount > 0:
            total_spent += transaction_amount

    cash_row_index = existing_portfolio.loc[existing_portfolio['ticker'] == 'Cash'].index[0]
    if isinstance(cash_row_index, pd.Index) and len(cash_row_index) > 0:
        cash_row_index = cash_row_index[0]
        existing_portfolio.at[cash_row_index, 'total_value'] -= total_spent
        existing_portfolio.at[cash_row_index, 'shares'] = existing_portfolio.at[cash_row_index, 'total_value']
    else:
    # If cash does not exist, add it
        cash_value = -total_spent
        existing_portfolio.loc[len(existing_portfolio)] = {'ticker': 'Cash', 'shares': cash_value, 'price': 1,
                                                       'total_value': cash_value}

    # Calculate total portfolio value
    total_value = existing_portfolio['total_value'].sum()

    # Calculate daily return
    previous_total_value = existing_portfolio.get('previous_total_value', total_value)
    daily_return = (total_value - previous_total_value) / previous_total_value
    existing_portfolio['previous_total_value'] = total_value
    existing_portfolio['daily_return'] = daily_return

    return existing_portfolio
