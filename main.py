from finvizfinance.screener.overview import Overview
from yahoo_fin.stock_info import get_data
from prophet import Prophet
from tqdm import tqdm
import matplotlib.pyplot as plt

foverview = Overview()
filters_dict = {"Price": "Over $10",
                "EPS growththis year": "Over 20%",
                "EPS growthqtr over qtr": "Over 20%",
                "EPS growthnext year": "Over 20%",
                "Sales growthqtr over qtr": "Positive (>0%)",
                "InstitutionalTransactions": "Positive (>0%)",
                "20-Day Simple Moving Average": "Price above SMA20",
                "50-Day Simple Moving Average": "Price above SMA50",
                "200-Day Simple Moving Average": "Price above SMA200",
                "RSI (14)": "Overbought (60)"}

foverview.set_filter(filters_dict=filters_dict)
pd = foverview.screener_view()

significant_stocks = []

for i in tqdm(range(pd.shape[0])):
    ticker = pd.iloc[i]['Ticker']
    data = get_data(ticker, start_date='01/01/2024')
    df = data['close'].reset_index()
    df.columns = ['ds', 'y']

    m = Prophet()
    m.fit(df)
    future = m.make_future_dataframe(periods=30)  # Adjust period as needed
    forecast = m.predict(future)

    # Analyze the trend
    trend_start = forecast['trend'].iloc[0]
    trend_end = forecast['trend'].iloc[-1]
    trend_slope = (trend_end - trend_start) / len(forecast)

    # Define your threshold for a significant positive trend
    significance_threshold = 0.8  # Example threshold

    if trend_slope >= significance_threshold:
        significant_stocks.append(ticker)
        fig = m.plot_components(forecast)
        fig2 = m.plot(forecast)
        fig.savefig(f'{ticker}_figure.png')
        fig2.savefig(f'{ticker}_figure2.png')
        plt.close(fig)
        plt.close(fig2)

    # Print or process the list of significant stocks
print(len(significant_stocks))
print("Stocks with Significant Positive Trend:", significant_stocks)
