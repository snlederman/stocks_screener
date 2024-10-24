CREATE TABLE IF NOT EXISTS historical_data (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10),
    date DATE,
    open FLOAT,
    high FLOAT,
    low FLOAT,
    close FLOAT,
    volume BIGINT,
    adj_close FLOAT,
    eps FLOAT,
    revenue FLOAT,

);