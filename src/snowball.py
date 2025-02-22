import json
from datetime import datetime, timedelta

import pysnowball as ball
import pandas as pd
import numpy as np
from src.indexes import all_stocks, example_color

import matplotlib.dates as mpd
import matplotlib.pylab as mpl
import matplotlib.pyplot as plt

mpl.rcParams['font.sans-serif'] = ['FangSong']
mpl.rcParams['axes.unicode_minus'] = False
plt.switch_backend('TkAgg')

"""
雪球接口封装
https://github.com/uname-yang/pysnowball、

# 设置token Cookie中的xq_a_token
ball.set_token("xq_a_tokene36746aa36d09ef01e900d02440657bf657ac97c;u=3376125439;")

# 实时行情
data = ball.quote_detail('SH600938')

# k线，历史x天
kline = ball.kline('SH600938', 300)
[
    "timestamp", 时间戳
    "open", 开盘
    "high", 最高
    "low", 最低
    "close", 收盘
    "chg", 涨跌额
    "percent", 涨跌幅
    "turnoverrate", 换手率
    "volume", 成交量
    "amount", 成交额
    "pe", 市盈率
    "pb", 市净率
    "ps", 市销率
    "pcf", 市现率
    "market_capital", 总市值
]

# 利润表 is_annals 只获取年报,默认为1 count 多少条
income = ball.income(symbol='SH600938', is_annals=1, count=10)
"""

ball.set_token("xq_a_token=efccba5b21eb83d54f69d1ec537bb060617c2f1b;u=3376125439;")

example_symbols = [
    ('SH510050', '上证50ETF'),
    ('SH000300', '沪深300'),
    ('SH511010', '国债ETF'),
    ('SH512100', '中证1000ETF'),
    ('SH512890', '红利低波ETF',),
    ('SH513630', '港股红利指数ETF'),
    ('SH515080', '中证红利ETF',),
    ('SH515100', '红利低波100ETF'),
    ('SH563300', '中证2000ETF'),
    ('SH600938', '中国海油'),
    ('01810', '小米集团'),
]

message_found = """\n%s(%s) 昨日收盘%s，昨日涨幅%s，近一年涨幅%s，180日均线偏离值%s"""


def render_message(symbol, df):
    close_last_year = df['close'].iloc[0]
    close = df['close'].iloc[-2]
    avg = df['avg'].iloc[-2]
    percent = df['percent'].iloc[-2]
    plz = round((close - avg) / avg * 100, 2)
    change = round((close - close_last_year) / close_last_year * 100, 2)
    return message_found % (
        symbol[1], symbol[0], f"{close}", f"{percent}%", f"{change}%", f"{plz}%",)


def send_message(msg):
    print(msg)


def download(symbols, start_date):
    start = datetime.strptime(start_date, '%Y%m%d')
    interval = (datetime.now() - start).days
    for symbol in symbols:
        kline = ball.kline(symbol, days=interval).get('data')
        df = pd.DataFrame(kline.get('item'), columns=kline.get('column'))
        df['日期Date'] = [datetime.fromtimestamp(t / 1000).strftime('%Y%m%d') for t in df['timestamp']]
        df['收盘Close'] = df['close']
        df['开盘Open'] = df['open']
        df['最高High'] = df['high']
        df['最低Low'] = df['low']
        df['涨跌幅PRT'] = df['percent']
        df['指数代码Index Code'] = [symbol for i in df['close']]
        with pd.ExcelWriter(f'../data/download_{symbol}.xlsx') as writer:
            columns = ['日期Date', '指数代码Index Code', '收盘Close', '开盘Open', '最高High', '最低Low']
            df.to_excel(writer, index=False, sheet_name='Data', columns=columns)
            print(f'download success {symbol}')


def get_index_data(symbols, start_date):
    start = datetime.strptime(start_date, '%Y%m%d')
    start_timestamp = start.timestamp() * 1000
    interval = (datetime.now() - start).days
    dfs = []
    for symbol in symbols:
        try:
            kline = ball.kline(symbol, days=interval).get('data')
            df = pd.DataFrame(kline.get('item'), columns=kline.get('column'))
            df['日期Date'] = [datetime.fromtimestamp(t / 1000).strftime('%Y%m%d') for t in df['timestamp']]
            df['收盘Close'] = df['close']
            df['开盘Open'] = df['open']
            df['最高High'] = df['high']
            df['最低Low'] = df['low']
            df['涨跌幅PRT'] = df['percent']
            df['指数代码Index Code'] = [symbol for i in df['close']]
            df = df[df['timestamp'] >= start_timestamp]
            # df.set_index('日期Date', inplace=True)
            dfs.append(df)
        except Exception as e:
            print(str(e))
    return dfs


def fetch_data(symbols, start_date):
    start = datetime.strptime(start_date, '%Y%m%d')
    start_timestamp = start.timestamp() * 1000
    interval = (datetime.now() - start).days
    dfs = []
    for symbol in symbols:
        kline = ball.kline(symbol, days=interval).get('data')
        df = pd.DataFrame(kline.get('item'), columns=kline.get('column'))
        df = df[df['timestamp'] >= start_timestamp]
        df['date'] = [datetime.fromtimestamp(t / 1000).strftime('%Y-%m-%d') for t in df['timestamp']]
        dfs.append(df)
        # with pd.ExcelWriter(f'../output/{symbol}_{start_date}.xlsx') as writer:
        #     columns = ['date', 'close', 'percent', 'timestamp']
        #     df.to_excel(writer, index=False, sheet_name='Data', columns=columns)
    return dfs


def render_chart(symbols, start_date):
    dfs = [pd.read_excel(f'../output/{symbol}_{start_date}.xlsx') for symbol in symbols]
    render(symbols, start_date, dfs, )


def render(symbols, start_date, dfs, avg=180):
    start = datetime.strptime(start_date, '%Y%m%d')
    start_timestamp = start.timestamp() * 1000
    # 时间对齐
    dfs = [df[df['timestamp'] >= start_timestamp] for df in dfs]
    # 起点对齐
    start_value = dfs[0]['close'].iloc[0]
    ratios = [start_value / df['close'].iloc[0] for df in dfs]

    plt.figure(figsize=(5 * 4, 5))
    message = "今天是%s，昨日股市表现如下" % (datetime.now().strftime('%Y年%m月%d日'))
    for i, df in enumerate(dfs):
        date_axis = pd.to_datetime(df['date'], format='%Y-%m-%d')
        symbol = None
        for s in all_stocks:
            if s[0]['symbol'] == symbols[i]:
                symbol = s
                break
        label = symbol[1] if symbol else symbols[i]
        df['avg'] = df['close'].rolling(window=avg).mean()
        plt.plot_date(date_axis, [x * ratios[i] for x in df['close']], '-', color=example_color[i], label=label)
        plt.plot_date(date_axis, [x * ratios[i] for x in df['avg']], '--', color=example_color[i], label=f'{label}_avg')
        message = message + render_message(symbol, df)

    plt.xlabel('交易日')
    plt.ylabel('收盘价')
    plt.legend(loc='upper left')
    plt.grid(True)
    # plt.show()
    plt.savefig(f'../output/render_dataframe_{start_date}.png', bbox_inches='tight')
    send_message(message)


# 对比多个指数的方法
def render_multi(symbols, start_date, end_date=None):
    dfs = get_index_data(symbols, start_date)
    dfs = sorted(dfs, key=lambda x: len(x.index), reverse=True)
    fdf = dfs[0]
    ratio = 1
    plt.figure(figsize=(5 * 4, 5))
    for i, df in enumerate(dfs):
        if end_date:
            end = datetime.strptime(end_date, '%Y%m%d')
            end_timestamp = end.timestamp() * 1000
            df = df[df['timestamp'] <= end_timestamp]
        date_axis = pd.to_datetime(df['日期Date'], format='%Y%m%d')
        symbol = df['指数代码Index Code'].iloc[0]
        if i != 0:
            fday = df['timestamp'].iloc[0]
            row = fdf[fdf['timestamp'] == fday]
            ratio = row['close'].iloc[0] / df['close'].iloc[0]
        plt.plot_date(date_axis, [x * ratio for x in df['close']], '-', label=symbol, color=example_color[i])
    plt.xlabel('交易日')
    plt.ylabel('收盘价')
    plt.legend(loc='upper left')
    plt.grid(True)
    filename = f'../output/render_multi_{start_date}.png'
    print(filename)
    plt.savefig(filename, bbox_inches='tight')


# 分析两个标的的阶段涨跌幅
def calc_range_percent(symbols, start_date, end_date=None, date_type=None):
    dfs = get_index_data(symbols, start_date)
    dfs = sorted(dfs, key=lambda x: len(x.index), reverse=True)
    new_dfs = []
    for i, df in enumerate(dfs):
        if end_date:
            end = datetime.strptime(end_date, '%Y%m%d')
            end_timestamp = end.timestamp() * 1000
            df = df[df['timestamp'] <= end_timestamp]
        symbol = df['指数代码Index Code'].iloc[0]
        df.rename(columns={'close': f'{symbol}_close', 'percent': f'{symbol}_percent'}, inplace=True)
        new_df = df[['日期Date', f'{symbol}_close', f'{symbol}_percent']]
        new_dfs.append(new_df)
    result = pd.concat(new_dfs, axis=1).drop_duplicates()
    name = "_".join(symbols)
    with pd.ExcelWriter(f'../output/compare_{name}.xlsx') as writer:
        result.to_excel(writer, index=False, sheet_name='Data')
        print(f'calc_range_percent success {name}')


# start_time = '20190101'
start_time = '20200101'
# start_time = '20220101'
# start_time = '20230101'
# start_time = '20240101'
# start_time = '20240901'
# end_time = '20220101'
end_time = None
# start_time = (datetime.now() - timedelta(days=366)).strftime('%Y%m%d')
symbol_list = [
    'SH510050', 'SH510300', 'SH510500', 'SH512100', 'SH512800', 'SH512890', 'SH515080', 'SH515100', 'SH563020',
    'SH563300', 'SH588000', 'SZ159338', 'SZ159555', 'SZ159593', 'SZ159915'
]

download(symbol_list, '20140101')

# render_multi(symbol_list, start_time, end_time)

# calc_range_percent(symbol_list, start_time, end_time)
