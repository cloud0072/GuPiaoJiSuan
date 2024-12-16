import datetime

import pysnowball as ball
import datetime
import numpy as np
import pandas as pd

import matplotlib.pylab as mpl

mpl.rcParams['font.sans-serif'] = ['FangSong']
mpl.rcParams['axes.unicode_minus'] = False
import matplotlib.pyplot as plt

plt.switch_backend('TkAgg')

ball.set_token("xq_a_token=a74d29b185741115b5e0b3a2d18e2b3f4ae8b9bc;u=3376125439;")

symbols1 = [('SH600938', '中国海油'), ('00883', '中国海洋石油'), ]
symbols2 = [('600941', '中国移动'), ('00941', '中国移动'), ]
symbols4 = [('601988', '中国银行'), ('03988', '中国银行'), ]
symbols5 = [('601318', '中国平安'), ('02318', '中国平安'), ]
symbols3 = [('600690', '海尔智家'), ('06690', '海尔智家'), ]


# # 实时行情
# dataA = ball.quote_detail('SH600938')
# # k线，历史x天
# lineA = ball.kline('SH600938', 300)
# # 利润表 is_annals 只获取年报,默认为1 count 多少条
# income = ball.income(symbol='SH600938', is_annals=1, count=10)


def render_ah(symbol_a, symbol_h, start_date):
    plt.figure(figsize=(16 * 5, 9))

    start = datetime.datetime.strptime(start_date, '%Y%m%d')
    interval = (datetime.datetime.now() - start).days
    start_timestamp = start.timestamp() * 1000
    line_a = ball.kline(symbol_a, interval).get('data')
    df_a = pd.DataFrame(line_a.get('item'), columns=line_a.get('column'))
    df_a = df_a[df_a['timestamp'] > start_timestamp]
    df_a['date'] = pd.to_datetime(df_a['timestamp'])
    a_close = df_a['close'].iloc[0]
    # date_a = [datetime.datetime.fromtimestamp(x / 1000) for x in df_a['timestamp']]
    plt.plot_date(df_a['date'], df_a['close'], '-', label=symbol_a, color="red")

    line_h = ball.kline(symbol_h, interval).get('data')
    df_h = pd.DataFrame(line_h.get('item'), columns=line_h.get('column'))
    df_h = df_h[df_h['timestamp'] > start_timestamp]
    df_h['date'] = pd.to_datetime(df_h['timestamp'])
    h_close = df_h['close'].iloc[0]
    # date_h = [datetime.datetime.fromtimestamp(x / 1000) for x in df_h['timestamp']]
    plt.plot_date(df_h['date'], [x / h_close * a_close for x in df_h['close']], '-', label=symbol_h, color="pink")

    # # 计算溢价比例
    # df_c = pd.read_excel('../data/结算汇兑比率.xlsx', sheet_name='结算汇兑比率')
    # df_c['currency_ratio'] = (df_c['买入结算汇兑比率'] + df_c['卖出结算汇兑比率']) / 2
    # df_c['timestamp'] = [datetime.datetime.strptime(x, '%Y-%m-%d').timestamp() for x in df_c['适用日期']]
    # ymin, ymax = plt.ylim()
    # # h_close = df_h['close'].iloc[0]
    # date_c = [datetime.datetime.fromtimestamp(x / 1000) for x in df_h['适用日期']]
    #
    # plt.plot_date(date_c, [ymax * x for x in df_h['currency_ratio']], '-', label=symbol_h, color="pink")

    plt.xlabel('交易日')
    plt.ylabel('收盘价')
    plt.legend(loc='upper right')

    plt.grid(True)
    plt.savefig(f'../output/image_snowball.png', bbox_inches='tight')


def render_ah2(symbol_a, symbol_h, start_date):
    plt.figure(figsize=(16 * 5, 9))

    start = datetime.datetime.strptime(start_date, '%Y%m%d')
    interval = (datetime.datetime.now() - start).days

    line_a = ball.kline(symbol_a, interval).get('data')
    df_a = pd.DataFrame(line_a.get('item'), columns=line_a.get('column'))
    df_a['date'] = [datetime.datetime.fromtimestamp(x / 1000) for x in df_a['timestamp']]

    line_h = ball.kline(symbol_h, interval).get('data')
    df_h = pd.DataFrame(line_h.get('item'), columns=line_h.get('column'))
    df_h['date'] = [datetime.datetime.fromtimestamp(x / 1000) for x in df_h['timestamp']]
    # # 计算溢价比例
    df_c = pd.read_excel('../data/结算汇兑比率.xlsx', sheet_name='结算汇兑比率')
    df_c['date'] = [datetime.datetime.strptime(x, '%Y-%m-%d') for x in df_c['适用日期']]
    df_c['currency_ratio'] = (df_c['买入结算汇兑比率'] + df_c['卖出结算汇兑比率']) / 2

    df1 = pd.DataFrame()
    df1['date'] = df_a['date']
    df1['close_a'] = df_a['close']
    df2 = pd.DataFrame()
    df2['date'] = df_h['date']
    df2['close_h'] = df_h['close']
    df3 = pd.DataFrame()
    df3['date'] = df_c['date']
    df3['currency_ratio'] = df_c['currency_ratio']
    df12 = pd.merge(df1, df2, on='date', how='outer')
    df123 = pd.merge(df12, df3, on='date', how='outer')

    start_a = df123['close_a'].iloc[0]
    start_h = df123['close_h'].iloc[0]

    plt.plot_date(df123['date'], df123['close_a'], '-', label=symbol_a, color="pink")
    plt.plot_date(df123['date'], [x / start_h * start_a for x in df123['close_h']], '-', label=symbol_h, color="pink")

    ymin, ymax = plt.ylim()
    plt.plot_date(df123['date'], [ymax * x for x in df123['currency_ratio']], '-', label=symbol_h, color="pink")

    plt.xlabel('交易日')
    plt.ylabel('收盘价')
    plt.legend(loc='upper right')

    plt.grid(True)
    plt.savefig(f'../output/image_snowball.png', bbox_inches='tight')


render_ah2('SH600938', '00883', '20231031')
# detail = ball.quote_detail('00883')
# detail = ball.main_indicator('SH600938')

# Index(['适用日期', '买入结算汇兑比率', '卖出结算汇兑比率', '货币种类'], dtype='object')
# detail = pd.read_excel('../data/结算汇兑比率.xlsx', sheet_name='结算汇兑比率')
# print(detail)
