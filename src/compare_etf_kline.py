import datetime

import numpy as np
import pandas as pd

import matplotlib.dates as mpd
import matplotlib.pylab as mpl
import matplotlib.pyplot as plt

from src.indexes import example_color

mpl.rcParams['font.sans-serif'] = ['FangSong']
mpl.rcParams['axes.unicode_minus'] = False
plt.switch_backend('TkAgg')


def get_index_data(symbols, start):
    start_date = datetime.datetime.strptime(start, '%Y%m%d')
    end_date = pd.Timestamp.now()
    dfs = []
    for symbol in symbols:
        try:
            df = pd.read_excel(f'../data/download_{symbol}.xlsx')
            df['date'] = pd.to_datetime(df['日期Date'], format='%Y%m%d')
            df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
            # df.set_index('日期Date', inplace=True)
            dfs.append(df)
        except Exception as e:
            print(str(e))
    return dfs


# 对比多个指数的方法
def render_multi(symbols, start_date, end_date=None):
    dfs = get_index_data(symbols, start_date)
    dfs = sorted(dfs, key=lambda x: len(x.index), reverse=True)
    fdf = dfs[0]
    ratio = 1
    plt.figure(figsize=(5 * 4, 5))
    for i, df in enumerate(dfs):
        if end_date:
            end = datetime.datetime.strptime(end_date, '%Y%m%d')
            df = df[df['date'] <= end]
        date_axis = pd.to_datetime(df['日期Date'], format='%Y%m%d')
        symbol = df['指数代码Index Code'].iloc[0]
        if i != 0:
            fday = df['date'].iloc[0]
            row = fdf[fdf['date'] == fday]
            ratio = row['收盘Close'].iloc[0] / df['收盘Close'].iloc[0]
        plt.plot_date(date_axis, [x * ratio for x in df['收盘Close']], '-', label=symbol, color=example_color[i])
    plt.xlabel('交易日')
    plt.ylabel('收盘价')
    plt.legend(loc='upper left')
    plt.grid(True)
    filename = f'../output/compare_etf_kline_{start_date}.png'
    plt.savefig(filename, bbox_inches='tight')


# 要对比的标的列表
symbol_list = [
    'SH510050',  # 上证50ETF
    'SH510300',  # 沪深300ETF
    'SH510500',  # 中证500ETF
    # 'SH512100',  # 中证1000ETF
    # 'SH563300',  # 中证2000ETF
    'SH588000',  # 科创50
    'SZ159915',  # 创业板ETF
    # 'SZ159593',  # 中证A50指数ETF
    # 'SZ159338',  # 中证A500ETF
    # 'SH512760',  # 芯片ETF
    # 'SH516160',  # 新能源ETF
    # 'SZ159928',  # 消费ETF
    # 'SH512800',  # 银行ETF
    # 'SH512890',  # 红利ETF
    # 'SH515080',  # 中证红利ETF
    # 'SH515100',  # 红利低波100ETF
    # 'SH563020',  # 红利低波动ETF
    # 'SZ159545',  # 恒生红利低波
    # "SH513630",  # 港股红利指数ETF
]
# start_date = (pd.Timestamp.now() - pd.DateOffset(years=1)).strftime("%Y%m%d")
# end_date = (pd.Timestamp.now() - pd.DateOffset(years=1)).strftime("%Y%m%d")

start_date = '20190101'
# end_date = '20240101'
end_date = None

render_multi(symbol_list, start_date=start_date, end_date=end_date)
# render_multi(symbol_list, start_date='20240101')
# render_multi(symbol_list, start_date='20190101')
