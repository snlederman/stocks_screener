from finvizfinance.screener.overview import Overview

filters_dict = {
    "Price": "Over $10",
    "EPS growththis year": "Over 20%",
    "EPS growthqtr over qtr": "Over 20%",
    "EPS growthnext year": "Over 20%",
    "Sales growthqtr over qtr": "Positive (>0%)",
    "InstitutionalTransactions": "Positive (>0%)",
    "20-Day Simple Moving Average": "Price above SMA20",
    "50-Day Simple Moving Average": "Price above SMA50",
    "200-Day Simple Moving Average": "Price above SMA200",
    "RSI (14)": "Overbought (60)"
}

def setup_overview(filters):
    """ Configures and returns an Overview object with predefined filters. """
    foverview = Overview()
    foverview.set_filter(filters_dict=filters)
    return foverview

overview = setup_overview(filters_dict)

# Fetch and display the data
df = overview.screener_view()
print(df)