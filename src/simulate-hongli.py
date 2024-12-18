import json
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

import matplotlib.pylab as mpl
import matplotlib.pyplot as plt

mpl.rcParams['font.sans-serif'] = ['FangSong']
mpl.rcParams['axes.unicode_minus'] = False

plt.switch_backend('TkAgg')

date_format = '%Y%m%d'
year_days = 244


def find_value(array, key, value):
    for item in array:
        if key in item and item[key] == value:
            return item
    return None


def computed_int_count(total, price):
    count = total / price
    return int(count / 100) * 100


def computed_grow(start, end):
    return round((end - start) / start * 100, 2)


def computed_ratio(start, end):
    return round((end - start) / end * 100, 2)


# 年化收益 每年交易日约等于243天
def computed_annualized(series, days):
    data_list = []
    # series = df['收盘Close']
    for i, row in series.iterrows():
        if i < days:
            data_list.append(0)
        else:
            oVal = series.iloc[i - days]
            nVal = series.iloc[i]
            data_list.append(computed_grow(oVal, nVal))
    return data_list


def read_csindex(start_date, codes):
    start_time = pd.to_datetime(start_date, format=date_format)
    result = []
    for code in codes.split(','):
        df = pd.read_excel(f'../data/download_{code}.xlsx', usecols=['日期Date', '收盘Close'])
        df['日期Date'] = pd.to_datetime(df['日期Date'], format=date_format)
        df['180天均线'] = df['收盘Close'].rolling(180).mean()
        # df['近6月收益率'] = computed_annualized(df['收盘Close'], int(year_days / 2))
        df['近一年收益率'] = computed_annualized(df['收盘Close'], year_days)
        # df['近两年收益率'] = computed_annualized(df['收盘Close'], year_days * 2)
        df = df[df['日期Date'] > start_time]
        df.index = range(1, len(df['日期Date']) + 1)
        result.append(df)
    return result


def read_snowball(start_date, codes):
    start_time = pd.to_datetime(start_date, format=date_format)
    result = []
    for code in codes.split(','):
        df = pd.read_excel(f'../data/snowball_{code}.xlsx', usecols=['date', 'close'])
        df['日期Date'] = pd.to_datetime(df['date'], format=date_format)
        df['收盘Close'] = df['close']
        df['180天均线'] = df['close'].rolling(180).mean()
        # df['近6月收益率'] = computed_annualized(df['close'], int(year_days / 2))
        df['近一年收益率'] = computed_annualized(df['close'], year_days)
        # df['近两年收益率'] = computed_annualized(df['close'], year_days * 2)
        df = df[df['日期Date'] > start_time]
        df.index = range(1, len(df['日期Date']) + 1)
        result.append(df)
    return result


def simulate_render():
    start = init_config.get('start')
    symbol = init_config.get('symbol')
    [df] = read_csindex(start, symbol)
    account = Account(init_config, df)
    account.computed()
    account.render()
    print(json.dumps({
        'warn_max': init_config.get('warn_max'),
        'warn_min': init_config.get('warn_min'),
        # 'ratio_delta': ratio_delta,
        'annual_grow': account.annual_grow(),
    }, ensure_ascii=False))


def simulate_range(range_start=-20, range_end=20, range_step: float = 1):
    start = init_config.get('start')
    symbol = init_config.get('symbol')
    ratio_delta = init_config.get('ratio_delta')
    [df] = read_csindex(start, symbol)

    # -18 ~ 28%
    start_list = []
    symbol_list = []
    max_list = []
    min_list = []
    annual_grow_list = []
    ratio_avg_list = []
    # ratio_delta_list = []

    for warn_max in np.arange(range_start, range_end, range_step):
        for warn_min in np.arange(range_start, warn_max + range_step, range_step):
            warn_max = float(warn_max)
            warn_min = float(warn_min)
            # for temp in range(0, 6):
            #     ratio_delta = temp / 2
            conf = {
                'warn_max': warn_max,
                'warn_min': warn_min,
                # 'ratio_delta': ratio_delta,
            }
            init_config.update(conf)
            account = Account(init_config, df)
            account.computed()
            annual_grow = account.annual_grow()
            ratio_avg = round(float(np.mean(account.z1)), 2)
            symbol_list.append(symbol)
            start_list.append(start)
            max_list.append(warn_max)
            min_list.append(warn_min)
            # ratio_delta_list.append(ratio_delta)
            annual_grow_list.append(annual_grow)
            ratio_avg_list.append(ratio_avg)
            print(json.dumps({
                'warn_max': warn_max,
                'warn_min': warn_min,
                # 'ratio_delta': ratio_delta,
                'annual_grow': annual_grow,
                'ratio_avg': ratio_avg,
            }, ensure_ascii=False))

    df = pd.DataFrame({
        'symbol': symbol_list,
        'start': start_list,
        'max': max_list,
        'min': min_list,
        # 'ratio_delta': ratio_delta_list,
        'annual_grow': annual_grow_list,
        'ratio_avg': ratio_avg_list,
    })
    df.to_excel(f'../output/simulate_{symbol}_{start}_{ratio_delta}.xlsx')


class Account:

    def __init__(self, config, df):
        self.df = df
        init_price = self.df['收盘Close'].iloc[0]
        init_money = config.get('init_money')
        init_percent = config.get('init_percent', 1)
        self.symbol = config.get('symbol')
        self.start = config.get('start')
        self.warn_max = config.get('warn_max', 12)
        self.warn_min = config.get('warn_min', 0)

        self.inventory = computed_int_count(init_money * init_percent, init_price)  # 初始持仓数量
        self.money = init_money - self.inventory * init_price  # 初始账户余额
        # self.loan_inventory = 0
        # self.loan_ratio = config.get('loan_ratio', 1.2)
        # self.loan_money = init_money * self.loan_ratio
        self.index = 0  # 序号
        self.deal_type = config.get('deal_type')
        self.ratio_delta = config.get('ratio_delta', 0)
        # self.deal_fee = 20  # 交易费用估算，限制频繁交易 20元

        self.z1 = []  # 历史持仓比例
        self.z2 = []  # 历史总余额
        self.z3 = []  # 历史总资产

    # 总市值 end为查看收盘市值
    def total_amount(self):
        return self.money + self.inventory * self.df['收盘Close'].iloc[self.index]

    def annual_grow(self):
        years = (self.df['日期Date'].iloc[-1] - self.df['日期Date'].iloc[0]).days / 365.25
        return round(((self.z3[-1] / self.z3[0]) ** (1 / years) - 1) * 100, 2)

    def computed(self):
        date_index = self.df['日期Date']
        # 计算
        for d in date_index:
            if self.deal_type == 1:
                self.computed_avg_next1()
            elif self.deal_type == 2:
                self.computed_annual_next1()
            self.index = self.index + 1
        self.index = self.index - 1

    def render(self):
        [hs300df] = read_csindex(self.start, '000300')
        df = self.df
        date_index = df['日期Date']
        amount_ratio = df['收盘Close'].iloc[0] / self.z3[0]
        hs300_ratio = df['收盘Close'].iloc[0] / hs300df['收盘Close'].iloc[0]

        fig, ax1 = plt.subplots(figsize=(4 * 10, 4))
        ax1.plot_date(date_index, df['收盘Close'], '-', label=self.symbol, color="red")
        ax1.plot_date(date_index, [x * hs300_ratio for x in hs300df['收盘Close']], '-', label='000300', color="orange")
        ax1.plot_date(date_index, df['180天均线'], '--', label="180天均线", color="pink")
        ax1.plot_date(date_index, [x * amount_ratio for x in self.z3], '-', label="总资产", color="darkred")

        ax2 = ax1.twinx()
        # avg_6m = df['近6月收益率'].mean()
        avg_year = df['近一年收益率'].mean()
        # avg_2year = df['近两年收益率'].mean()

        # ax2.plot_date(date_index, df['近6月收益率'], '--', label="avg_6m", color="skyblue")
        # ax2.plot_date(date_index, [avg_6m for d in date_index], '--', label="平均收益率", color="skyblue")
        ax2.plot_date(date_index, df['近一年收益率'], '--', label="近一年收益率", color="skyblue")
        ax2.plot_date(date_index, [avg_year for d in date_index], '--', label="平均收益率", color="skyblue")
        # ax2.plot_date(date_index, df['近两年收益率'], '--', label="近两年收益率", color="blue")
        # ax2.plot_date(date_index, [avg_2year for d in date_index], '--', label="平均收益率", color="blue")
        ax2.plot_date(date_index, self.z1, '--', label="比例", color="darkblue")

        # ax.xlabel('交易日')
        # ax.ylabel('收盘价')
        # ax.legend(loc='upper right')
        # ax.xaxis.set_major_locator(mdates.DayLocator())

        ax1.grid(True)
        plt.savefig(f'../output/image_hongli_{self.symbol}_{self.start}.png', bbox_inches='tight')

    """
        年化12%业绩比较基准+-3%进行调仓
        最大值28%
        最小值-18%
        平均值9%
    """

    def computed_annual_next1(self):
        factor_100 = 100
        factor_50 = 50
        price = self.df['收盘Close'].iloc[self.index]  # 获取当天收盘价
        # annual = self.df['近6月收益率'].iloc[self.index]
        annual = self.df['近一年收益率'].iloc[self.index]
        # annual = self.df['近两年收益率'].iloc[self.index]
        total_money = self.total_amount()
        warn_max = self.warn_max
        warn_min = self.warn_min

        ratio = computed_ratio(self.money, total_money)
        if annual <= warn_min and ratio < (factor_100 - self.ratio_delta):
            factor = factor_100
        elif warn_min < annual <= warn_max and (
                ratio > (factor_50 + self.ratio_delta) or ratio < (factor_50 - self.ratio_delta)):
            factor = factor_50
        elif warn_max < annual:
            factor = 0
        else:
            factor = ratio
        try:
            money_delta = self.money - total_money * (1 - factor / 100)
            count_delta = computed_int_count(money_delta, price)
            self.inventory = self.inventory + count_delta
            self.money = self.money - count_delta * price
        except Exception as e:
            print(e)

        total_money = self.total_amount()
        ratio = computed_ratio(self.money, total_money)

        self.z1.append(ratio)
        self.z2.append(self.money)
        self.z3.append(total_money)

    def computed_avg_next1(self):
        factor_100 = 100
        factor_50 = 50
        price = self.df['收盘Close'].iloc[self.index]  # 获取当天收盘价
        avg = self.df['180天均线'].iloc[self.index]  # 获取当天收盘价
        total_money = self.total_amount()
        warn_max = self.warn_max
        warn_min = self.warn_min
        delta = computed_grow(price, avg)  # 均线偏离值

        ratio = computed_ratio(self.money, total_money)
        if delta <= warn_min and ratio < (factor_100 - self.ratio_delta):
            factor = factor_100
        elif warn_min < delta <= warn_max and (
                ratio > (factor_50 + self.ratio_delta) or ratio < (factor_50 - self.ratio_delta)):
            factor = factor_50
        elif warn_max < delta:
            factor = 0
        else:
            factor = ratio
        try:
            money_delta = self.money - total_money * (1 - factor / 100)
            count_delta = computed_int_count(money_delta, price)
            self.inventory = self.inventory + count_delta
            self.money = self.money - count_delta * price
        except Exception as e:
            print(e)

        total_money = self.total_amount()
        ratio = computed_ratio(self.money, total_money)

        self.z1.append(ratio)
        self.z2.append(self.money)
        self.z3.append(total_money)


symbols = [
    ('沪深300', '000300'),
    ('红利低波全收益', 'H20269'),
    ('红利低波100全收益', 'H20955'),
    ('中证红利', '000922CNY020'),
    ('港股通高股息', '930914CNY220'),
    ('香港红利', '932335'),
    ('沪港深红利低波', '930993'),
    ('沪港深高股息100', '921445'),
    ('香港海外高股息', 'H20908'),
]
etfs = [
    ('中证红利ETF', '515080'),
    ('红利低波ETF', '512890'),
]
init_config = {
    # 'symbol': '000300',
    # 'symbol': 'H20269',
    'symbol': 'H20955',
    # 'symbol': '000922CNY020',
    'start': '20181216',
    'init_money': 100_0000_0000,
    'init_percent': 1,
    # 'deal_type': 1,  # 均线
    'deal_type': 2,  # 年化
    'warn_max': 9.5,
    'warn_min': 9.5,
    'ratio_delta': 0,
}

if __name__ == '__main__':
    # simulate_render()
    # simulate_range(-30, -10)
    simulate_range(6, 24, 0.5)
