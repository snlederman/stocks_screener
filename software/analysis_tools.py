from prophet import Prophet

FORECAST_PERIODS = 30
def prepare_data(data):
    """Prepare data for Prophet modeling."""
    df = data.reset_index()
    df.columns = ['ds', 'y']
    return df


def prepare_and_forecast_model(data, periods):
    """Analyzes trends over specified periods and forecasts using Prophet."""
    slopes = []
    for period in periods:
        if len(data) >= period:
            df = prepare_data(data)
            model = Prophet()
            model.fit(df.iloc[len(data)-period:].reset_index(drop=True))
            future = model.make_future_dataframe(periods=FORECAST_PERIODS)
            forecast = model.predict(future)
            trend_start = forecast.iloc[-FORECAST_PERIODS]['trend']
            trend_end = forecast.iloc[-1]['trend']
            slope = (trend_end - trend_start) / FORECAST_PERIODS
            slopes.append(slope)
    return slopes
