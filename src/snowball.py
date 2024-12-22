from datetime import datetime, timedelta

import pysnowball as ball
import pandas as pd
import numpy as np

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

ball.set_token("xq_a_token=2420c49cd18e847d63cec9744fd29e638ff2a540;u=3376125439;")

example_symbols = [
    ('SH000300', '沪深300'),
    ('SH511010', '国债ETF'),
    ('SH512100', '中证1000ETF'),
    ('SH515080', '中证红利ETF', 1.571),
    ('SH515100', '红利低波100ETF', 1.51),
    ('SH513630', '港股红利指数ETF', 1.288),
    ('SH563300', '中证2000ETF', 1.144),
    ('SH600938', '中国海油'),
    ('01810', '小米集团'),
    ('515080', '中证红利ETF',),
    ('512890', '红利低波ETF',),
]

example_color = [
    '#ff1908',
    '#f5642c',
    '#faad14',
    '#1677ff',
    '#00b96b',
    '#f02b99',
    '#8b70f1',
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
        df['指数代码Index Code'] = [symbol for i in df['close']]
        with pd.ExcelWriter(f'../data/download_{symbol}.xlsx') as writer:
            columns = ['日期Date', '指数代码Index Code', '收盘Close']
            df.to_excel(writer, index=False, sheet_name='Data', columns=columns)


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
        for s in example_symbols:
            if s[0] == symbols[i]:
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
    plt.savefig(f'../output/render_dataframe_{start_time}.png', bbox_inches='tight')
    send_message(message)


if __name__ == '__main__':
    start_time = (datetime.now() - timedelta(days=366)).strftime('%Y%m%d')
    symbol_list = ['SH000300', 'SH515100', 'SH513630', 'SH563300', 'SH515080', 'SH512890']
    # start_time = '20201201'
    # symbol_list = ['SH512100', 'SH515100', 'SH515080']
    # df_list = fetch_data(symbol_list, start_time)
    # render(symbol_list, start_time, df_list, )
    download(symbol_list, '20131218')
