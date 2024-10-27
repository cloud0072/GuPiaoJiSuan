import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# 获取Apple的股票数据
data = yf.download('AAPL', start='2020-01-01', end='2023-07-01')

# 绘制K线图
data['Close'].plot(kind='candle', grid=True, ylim=(0, 100))

# 显示图表
plt.show()