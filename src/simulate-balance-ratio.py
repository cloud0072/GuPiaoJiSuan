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
    return round(start / end * 100, 2)


# 年化收益 每年交易日约等于243天
def computed_annualized(series, days):
    data_list = []
    for i, row in enumerate(series):
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
        df = pd.read_excel(f'../data/download_{code}.xlsx', usecols=['日期Date', '收盘Close', '最高High', '最低Low'])
        df['日期Date'] = pd.to_datetime(df['日期Date'], format=date_format)
        df['60天均线'] = df['收盘Close'].rolling(60).mean()
        df['180天均线'] = df['收盘Close'].rolling(180).mean()
        df['360天均线'] = df['收盘Close'].rolling(360).mean()
        df['近一年均线'] = df['收盘Close'].rolling(year_days).mean()
        df = df[df['日期Date'] > start_time]
        df.index = range(1, len(df['日期Date']) + 1)
        result.append(df)
    return result


def simulate_render(deal_type=1, symbol1=None, symbol2=None, ratio_balance=None, ratio_deal=None):
    if deal_type:
        init_config.update({'deal_type': deal_type})
    if symbol1:
        init_config.update({'symbol1': symbol1})
    if symbol2:
        init_config.update({'symbol2': symbol2})
    if ratio_balance:
        init_config.update({'ratio_balance': ratio_balance})
    if ratio_deal:
        init_config.update({'ratio_deal': ratio_deal})
    start = init_config.get('start')
    symbol1 = init_config.get('symbol1')
    symbol2 = init_config.get('symbol2')
    [df, df2] = read_csindex(start, f"{symbol1},{symbol2}")
    account = Account(init_config, df, df2)
    account.enable_log = True
    account.computed()
    account.render()
    print(json.dumps({
        'deal_type': init_config.get('deal_type'),
        'ratio_balance': init_config.get('ratio_balance'),
        'ratio_deal': init_config.get('ratio_deal'),
        'annual_grow': account.annual_grow(),
        'total_grow': computed_grow(account.z3[0], account.z3[-1]),
    }, ensure_ascii=False))


# def simulate_range(conf_step, conf_ratio, range_step):
#     start = init_config.get('start')
#     symbol = init_config.get('symbol')
#     deal_type = init_config.get('deal_type')
#     [df] = read_csindex(start, symbol)
#
#     start_list = []
#     symbol_list = []
#     grid_step_list = []
#     grid_ratio_list = []
#     annual_grow_list = []
#     ratio_avg_list = []
#
#     for grid_step in np.arange(conf_step[0], conf_step[1], range_step):
#         for grid_ratio in np.arange(conf_ratio[0], conf_ratio[1], range_step):
#             grid_step = float(grid_step)
#             grid_ratio = float(grid_ratio)
#             conf = {
#                 'grid_step': grid_step,
#                 'grid_ratio': grid_ratio,
#             }
#             init_config.update(conf)
#             account = Account(init_config, df)
#             account.enable_log = False
#             account.computed()
#             annual_grow = account.annual_grow()
#             ratio_avg = round(float(np.mean(account.z1)), 2)
#             symbol_list.append(symbol)
#             start_list.append(start)
#             grid_step_list.append(grid_step)
#             grid_ratio_list.append(grid_ratio)
#             annual_grow_list.append(annual_grow)
#             ratio_avg_list.append(ratio_avg)
#             print(json.dumps({
#                 'grid_step': grid_step,
#                 'grid_ratio': grid_ratio,
#                 'annual_grow': annual_grow,
#                 'ratio_avg': ratio_avg,
#             }, ensure_ascii=False))
#
#     df = pd.DataFrame({
#         'symbol': symbol_list,
#         'start': start_list,
#         'grid_step': grid_step_list,
#         'grid_ratio': grid_ratio_list,
#         'annual_grow': annual_grow_list,
#         'ratio_avg': ratio_avg_list,
#     })
#     df.to_excel(f'../output/simulate_{symbol}_{start}_{deal_type}.xlsx')


class Account:

    def __init__(self, config, df1, df2):
        self.enable_log = False
        self.df1 = df1
        self.df2 = df2

        price1 = self.df1['收盘Close'].iloc[0]
        price2 = self.df2['收盘Close'].iloc[0]
        init_money = config.get('init_money')
        self.start = config.get('start')
        # init_percent = config.get('init_percent', 0.8)
        self.symbol1 = config.get('symbol1')
        self.symbol2 = config.get('symbol2')
        self.ratio_balance = config.get('ratio_balance')
        self.ratio_deal = config.get('ratio_deal')
        self.deal_type = config.get('deal_type')

        self.inventory1 = computed_int_count(init_money * self.ratio_balance, price1)  # 初始持仓数量
        self.money = init_money - self.inventory1 * price1  # 初始账户余额

        self.inventory2 = computed_int_count(self.money, price2)  # 初始持仓数量
        self.money = self.money - self.inventory2 * price2  # 初始账户余额

        self.index = 0  # 序号

        self.z1 = []  # 历史持仓比例
        self.z2 = []  # 历史总余额
        self.z3 = []  # 历史总资产

    # 总市值 end为查看收盘市值
    def total_amount(self):
        price1 = self.df1['收盘Close'].iloc[self.index]
        price2 = self.df2['收盘Close'].iloc[self.index]
        return self.money + self.inventory1 * price1 + self.inventory2 * price2

    def annual_grow(self):
        years = (self.df1['日期Date'].iloc[-1] - self.df1['日期Date'].iloc[0]).days / 365.25
        return round(((self.z3[-1] / self.z3[0]) ** (1 / years) - 1) * 100, 2)

    def computed(self):
        date_index = self.df1['日期Date']
        # 计算
        for d in date_index:
            if self.deal_type == 1:
                self.computed_type_1()
            self.index = self.index + 1
        self.index = self.index - 1

    def render(self):
        symbol1 = init_config.get('symbol1')
        symbol2 = init_config.get('symbol2')
        df1 = self.df1
        df2 = self.df2
        date_index = df1['日期Date']
        symbol2_ratio = df1['收盘Close'].iloc[0] / df2['收盘Close'].iloc[0]
        amount_ratio = df1['收盘Close'].iloc[0] / self.z3[0]

        fig, ax1 = plt.subplots(figsize=(4 * 10, 4))
        ax1.plot_date(date_index, df1['收盘Close'], '-', label=symbol1, color="red")
        ax1.plot_date(date_index, [x * symbol2_ratio for x in df2['收盘Close']], '-', label=symbol2, color="orange")
        # ax1.plot_date(date_index, df['60天均线'], '--', label="60天均线", color="red")
        ax1.plot_date(date_index, df1['180天均线'], '--', label="180天均线", color="red")
        # ax1.plot_date(date_index, df['360天均线'], '--', label="360天均线", color="darkred")
        # ax1.plot_date(date_index, [x * hs300_ratio for x in hs300df['收盘Close']], '-', label='000300', color="orange")
        ax1.plot_date(date_index, [x * amount_ratio for x in self.z3], '-', label="总资产", color="darkred")

        ax2 = ax1.twinx()
        ax2.plot_date(date_index, self.z1, '--', label="比例", color="darkblue")
        # ax2.plot_date(date_index, [avg_year for d in date_index], '--', label="平均收益率", color="skyblue")

        # ax.xlabel('交易日')
        # ax.ylabel('收盘价')
        # ax.legend(loc='upper right')
        # ax.xaxis.set_major_locator(mdates.DayLocator())

        ax1.grid(True)
        plt.savefig(f'../output/image_balance_{symbol1}_{self.start}_{self.deal_type}.png', bbox_inches='tight')

    """
        网格交易 根据标的最大波动幅度设置网格
        根据均线优化网格
    """

    def computed_type_1(self):
        date = self.df1['日期Date'].iloc[self.index]
        price1 = self.df1['收盘Close'].iloc[self.index]
        price2 = self.df2['收盘Close'].iloc[self.index]
        total_money = self.total_amount()

        ratio1 = computed_ratio(self.inventory1 * price1, total_money)
        ratio2 = computed_ratio(self.inventory2 * price2, total_money)
        if ratio1 >= self.ratio_deal or ratio2 >= self.ratio_deal:
            # 资产涨幅较大，卖出
            inventory1 = computed_int_count(total_money * self.ratio_balance, price1)
            money_left = total_money - inventory1 * price1
            inventory2 = computed_int_count(money_left, price2)
            self.money = money_left - inventory2 * price2
            delta_count1 = self.inventory1 - inventory1
            delta_count2 = self.inventory2 - inventory2
            self.inventory1 = inventory1
            self.inventory2 = inventory2
            if self.enable_log:
                print(json.dumps({
                    'date': date.strftime('%Y%m%d'),
                    'price1': price1,
                    'delta_count1': delta_count1,
                    'price2': price2,
                    'delta_count2': delta_count2,
                }, ensure_ascii=False))
        else:
            pass

        ratio1 = computed_ratio(self.inventory1 * price1, total_money)

        self.z1.append(ratio1)
        self.z2.append(self.money)
        self.z3.append(total_money)


init_config = {
    'init_money': 100_0000_0000,
    'start': '20141216',
    'symbol1': '000300',
    # 'symbol': '000905',
    # 'symbol': '000852',
    'symbol2': 'H20269',
    'ratio_balance': 0.5,
    'ratio_deal': 70,
    'deal_type': 1,  # 按总资产的百分比网格
}

if __name__ == '__main__':
    simulate_render(deal_type=1, symbol1='000300', symbol2='H20269', ratio_balance=0.5, ratio_deal=60)
