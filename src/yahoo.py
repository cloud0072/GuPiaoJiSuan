from datetime import datetime

import yfinance as yf


def get_history(symbol, start_date='2024-01-01'):
    h = yf.Ticker(symbol)
    data = h.history(start=start_date, end=datetime.now().strftime('%Y-%m-%d'))
    print(data)

# 上证指数
get_history('000001.SS')
