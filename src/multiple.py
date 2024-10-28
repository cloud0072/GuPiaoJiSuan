import datetime

import matplotlib.pylab as mpl
import pandas

mpl.rcParams['font.sans-serif'] = ['FangSong']
mpl.rcParams['axes.unicode_minus'] = False
import matplotlib.pyplot as plt
import numpy as np

plt.switch_backend('TkAgg')


def find_value(array, key, value):
    for item in array:
        if key in item and item[key] == value:
            return item
    return None


def read(start_date, codes):
    result = []
    for code in codes.split(','):
        df = pandas.read_excel(f'../data/download_{code}.xlsx')
        result.append(df[df['日期Date'] > int(start_date.strftime('%Y%m%d'))])
    return result


def render_multiple():
    start_date = datetime.datetime.strptime('20181028', '%Y%m%d')
    [hs300df, hl100df, hlqzdf] = read(start_date, '000300,H20955,H20269')
    hl100df['180天均线'] = hl100df['收盘Close'].rolling(window=180).mean()
    date300 = pandas.to_datetime(hs300df['日期Date'], format='%Y%m%d')
    date100 = pandas.to_datetime(hl100df['日期Date'], format='%Y%m%d')
    # datehlqz = pandas.to_datetime(hlqzdf['日期Date'], format='%Y%m%d')

    hs300_f = hs300df['收盘Close'].iloc[0]
    hl100_f = hl100df['收盘Close'].iloc[0]
    # hlqz_f = hlqzdf['收盘Close'].iloc[0]

    plt.figure(figsize=(16 * 2, 9))
    plt.plot_date(date100, hl100df['收盘Close'], '-', label="H20955", color="red")
    plt.plot_date(date100, hl100df['180天均线'], '--', label="180天均线", color="pink")

    plt.plot_date(date300, [(x / hs300_f * hl100_f) for x in hs300df['收盘Close']], '-', label="000300", color="darkred")
    # plt.plot_date(datehlqz, [(x / hlqz_f * hl100_f) for x in hlqzdf['收盘Close']], '-', label="H20269", color="orange")

    plt.xlabel('交易日')
    plt.ylabel('收盘价')
    plt.legend(loc='upper right')

    plt.grid(True)
    plt.savefig(f'../output/image_multiple.png', bbox_inches='tight')


def computed_int_count(total, price):
    count = total / price
    return int(count / 100) * 100


def computed_round(start, end):
    return round((end - start) / start * 100, 2)


class Account():

    def __init__(self, config, dataframe):
        self.df = dataframe

        init_money = config.get('init_money')
        self.init_percent = config.get('init_percent')
        self.inventory = computed_int_count(init_money * self.init_percent, self.base_price)  # 初始持仓数量
        self.money = init_money - self.inventory * self.base_price  # 初始账户余额
        self.index = 0  # 序号
        self.deal_type = config.get('deal_type')
        # self.deal_fee = 20  # 交易费用估算，限制频繁交易 20元

        self.z1 = []  # 历史持仓比例
        self.z2 = []  # 历史总余额
        self.z3 = []  # 历史总资产

    # 总市值 end为查看收盘市值
    def total_amount(self):
        return self.money + self.inventory * self.df['收盘Close'].iloc(self.index)

    def computed_date_next(self):
        price = self.df['收盘Close'].iloc(self.index)  # 获取当天收盘价
        total_money = self.total_amount()

        # self.

        self.z1.append(round((total_money - self.money) / total_money, 2))
        self.z2.append(self.money)
        self.z3.append(total_money)
        self.index = self.index + 1  # 加一天


render_multiple()
