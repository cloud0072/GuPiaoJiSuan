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
        df['180天均线'] = df['收盘Close'].rolling(180).mean()
        df['近一年均线'] = df['收盘Close'].rolling(year_days).mean()
        df['近两年均线'] = df['收盘Close'].rolling(year_days * 2).mean()
        df = df[df['日期Date'] > start_time]
        df.index = range(1, len(df['日期Date']) + 1)
        result.append(df)
    return result


def simulate_render(grid_step=None, grid_ratio=None, deal_type=None, symbol=None):
    if grid_step:
        init_config.update({'grid_step': grid_step})
    if grid_ratio:
        init_config.update({'grid_ratio': grid_ratio})
    if deal_type:
        init_config.update({'deal_type': deal_type})
    if symbol:
        init_config.update({'symbol': symbol})
    start = init_config.get('start')
    symbol = init_config.get('symbol')
    [df] = read_csindex(start, symbol)
    account = Account(init_config, df)
    account.enable_log = True
    account.computed()
    account.render()
    print(json.dumps({
        'grid_step': init_config.get('grid_step'),
        'grid_ratio': init_config.get('grid_ratio'),
        'annual_grow': account.annual_grow(),
        'ratio_avg': round(float(np.mean(account.z1)), 2),
        'index_grow': computed_grow(account.df['收盘Close'].iloc[0], account.df['收盘Close'].iloc[-1]),
        'total_grow': computed_grow(account.z3[0], account.z3[-1]),
    }, ensure_ascii=False))


def simulate_range(conf_step, conf_ratio, range_step):
    start = init_config.get('start')
    symbol = init_config.get('symbol')
    deal_type = init_config.get('deal_type')
    [df] = read_csindex(start, symbol)

    start_list = []
    symbol_list = []
    grid_step_list = []
    grid_ratio_list = []
    annual_grow_list = []
    ratio_avg_list = []

    for grid_step in np.arange(conf_step[0], conf_step[1], range_step):
        for grid_ratio in np.arange(conf_ratio[0], conf_ratio[1], range_step):
            grid_step = float(grid_step)
            grid_ratio = float(grid_ratio)
            conf = {
                'grid_step': grid_step,
                'grid_ratio': grid_ratio,
            }
            init_config.update(conf)
            account = Account(init_config, df)
            account.enable_log = False
            account.computed()
            annual_grow = account.annual_grow()
            ratio_avg = round(float(np.mean(account.z1)), 2)
            symbol_list.append(symbol)
            start_list.append(start)
            grid_step_list.append(grid_step)
            grid_ratio_list.append(grid_ratio)
            annual_grow_list.append(annual_grow)
            ratio_avg_list.append(ratio_avg)
            print(json.dumps({
                'grid_step': grid_step,
                'grid_ratio': grid_ratio,
                'annual_grow': annual_grow,
                'ratio_avg': ratio_avg,
            }, ensure_ascii=False))

    df = pd.DataFrame({
        'symbol': symbol_list,
        'start': start_list,
        'grid_step': grid_step_list,
        'grid_ratio': grid_ratio_list,
        'annual_grow': annual_grow_list,
        'ratio_avg': ratio_avg_list,
    })
    df.to_excel(f'../output/simulate_{symbol}_{start}_{deal_type}.xlsx')


class Account:

    def __init__(self, config, df):
        self.enable_log = False
        self.df = df
        init_price = self.df['收盘Close'].iloc[0]
        init_money = config.get('init_money')
        init_percent = config.get('init_percent', 0.8)
        self.symbol = config.get('symbol')
        self.start = config.get('start')
        self.grid_value = init_price
        self.grid_step = config.get('grid_step', 5)
        self.grid_ratio = config.get('grid_ratio', 10)

        self.inventory = computed_int_count(init_money * init_percent, init_price)  # 初始持仓数量
        self.money = init_money - self.inventory * init_price  # 初始账户余额
        # self.loan_inventory = 0
        # self.loan_ratio = config.get('loan_ratio', 1.2)
        # self.loan_money = init_money * self.loan_ratio
        self.index = 0  # 序号
        self.deal_type = config.get('deal_type')

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
            elif self.deal_type == 5:
                self.computed_avg_next5()
            elif self.deal_type == 6:
                self.computed_avg_next6()
            else:
                raise SystemError('未找到合适的策略')
            self.index = self.index + 1
        self.index = self.index - 1

    def render(self):
        df = self.df
        date_index = df['日期Date']
        amount_ratio = df['收盘Close'].iloc[0] / self.z3[0]

        fig, ax1 = plt.subplots(figsize=(4 * 10, 4))
        ax1.plot_date(date_index, df['收盘Close'], '-', label=self.symbol, color="red")
        # ax1.plot_date(date_index, df['180天均线'], '--', label="180天均线", color="red")
        # ax1.plot_date(date_index, df['近一年均线'], '--', label="近一年均线", color="red")
        ax1.plot_date(date_index, df['近两年均线'], '--', label="近两年均线", color="red")
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
        plt.savefig(f'../output/image_grid_{self.symbol}_{self.start}_{self.deal_type}.png', bbox_inches='tight')

    """
        网格交易 根据标的最大波动幅度设置网格
        根据均线优化网格
    """

    def computed_avg_next1(self):
        date = self.df['日期Date'].iloc[self.index]
        price_high = self.df['最高High'].iloc[self.index]
        price_low = self.df['最低Low'].iloc[self.index]
        total_money = self.total_amount()
        grid_value = self.grid_value
        grid_step = self.grid_step
        grid_ratio = self.grid_ratio

        ratio = computed_ratio(self.money, total_money)
        price_sell = round(grid_value * (100 + grid_step) / 100, 2)
        price_buy = round(grid_value * (100 - grid_step) / 100, 2)
        if price_sell <= price_high:
            # 大于网格卖出
            self.grid_value = price_sell
            factor = ratio - grid_ratio
        elif price_low <= price_buy:
            # 低于网格买入
            self.grid_value = price_buy
            factor = ratio + grid_ratio
        else:
            factor = ratio
        try:
            if factor != ratio:
                factor = 0 if factor < 0 else 100 if factor > 100 else factor
                money_delta = self.money - total_money * (1 - factor / 100)
                count_delta = computed_int_count(money_delta, self.grid_value)
                self.inventory = self.inventory + count_delta
                self.money = self.money - count_delta * self.grid_value

                if self.enable_log:
                    print(json.dumps({
                        'date': date.strftime('%Y%m%d'),
                        'price': self.grid_value,
                        'count_delta': count_delta,
                        'factor': round(factor, 2),
                    }, ensure_ascii=False))
        except Exception as e:
            print(e)

        total_money = self.total_amount()
        ratio = computed_ratio(self.money, total_money)

        self.z1.append(ratio)
        self.z2.append(self.money)
        self.z3.append(total_money)

    # 按持仓比例买卖
    def computed_avg_next5(self):
        date = self.df['日期Date'].iloc[self.index]
        price_close = self.df['收盘Close'].iloc[self.index]
        price_high = self.df['最高High'].iloc[self.index]
        price_high = price_close if np.isnan(price_high) else price_high
        price_low = self.df['最低Low'].iloc[self.index]
        price_low = price_close if np.isnan(price_low) else price_low
        # avg = self.df['180天均线'].iloc[self.index]
        avg = self.df['近一年均线'].iloc[self.index]
        total_money = self.total_amount()
        grid_value = self.grid_value
        grid_step = self.grid_step
        grid_ratio = self.grid_ratio

        ratio = computed_ratio(self.money, total_money)
        price_sell = round(grid_value * (100 + grid_step) / 100, 2)
        price_buy = round(grid_value * (100 - grid_step) / 100, 2)
        n = 0
        if price_sell <= price_high and self.inventory > 0:
            # 大于网格卖出
            self.grid_value = price_sell  # 成交价设置为新的网格价
            # 均线高于价格 正常卖出
            # 均线低于价格 增加偏离值的卖出量
            delta = round((price_sell - avg) / avg, 2) if avg < price_sell else 0
            n = 1 + delta * 2  # 设置影响因子 - 卖出价大于均线比例越高则卖出越多，卖出价小于均线则降低
            factor = ratio - grid_ratio * n
        elif price_low <= price_buy and self.money > 100 * price_buy:
            # 低于网格买入
            self.grid_value = price_buy
            # 均线高于价格 增加偏离值的买入出量
            # 均线低于价格 正常买入
            delta = round((avg - price_buy) / price_buy, 2) if avg > price_buy else 0
            n = 1 + delta * 4  # 设置影响因子 - 卖出价大于均线比例越高则卖出越多，卖出价小于均线则降低
            factor = ratio + grid_ratio * n
        else:
            factor = ratio
        try:
            if factor != ratio:
                factor = 0 if factor < 0 else 100 if factor > 100 else factor  # 买卖超过持仓最大最小值时进行修正
                money_delta = self.money - total_money * (1 - factor / 100)
                count_delta = computed_int_count(money_delta, self.grid_value)
                self.inventory = self.inventory + count_delta
                self.money = self.money - count_delta * self.grid_value

                if self.enable_log:
                    print(json.dumps({
                        'date': date.strftime('%Y%m%d'),
                        'price': self.grid_value,
                        'count_delta': count_delta,
                        'factor': round(factor, 2),
                        'n': round(n, 2),
                        'avg': round(avg, 2),
                    }, ensure_ascii=False))
        except Exception as e:
            print(e)

        total_money = self.total_amount()
        ratio = computed_ratio(self.money, total_money)

        self.z1.append(ratio)
        self.z2.append(self.money)
        self.z3.append(total_money)

    # 按持仓比例买卖
    def computed_avg_next6(self):
        date = self.df['日期Date'].iloc[self.index]
        price_close = self.df['收盘Close'].iloc[self.index]
        price_high = self.df['最高High'].iloc[self.index]
        price_high = price_close if np.isnan(price_high) else price_high
        price_low = self.df['最低Low'].iloc[self.index]
        price_low = price_close if np.isnan(price_low) else price_low
        # avg = self.df['180天均线'].iloc[self.index]
        avg = self.df['近两年均线'].iloc[self.index]
        total_money = self.total_amount()
        grid_value = self.grid_value
        grid_step = self.grid_step
        grid_ratio = self.grid_ratio

        ratio = computed_ratio(self.money, total_money)
        price_sell = round(grid_value * (100 + grid_step) / 100, 2)
        price_buy = round(grid_value * (100 - grid_step) / 100, 2)
        n = 0
        if price_sell <= price_high and self.inventory > 0:
            # 大于网格卖出
            self.grid_value = price_sell  # 成交价设置为新的网格价
            # 均线高于价格 正常卖出
            # 均线低于价格 增加偏离值的卖出量
            delta = round((price_sell - avg) / avg, 2) if avg < price_sell else 0
            n = 1 + delta * 2  # 设置影响因子 - 卖出价大于均线比例越高则卖出越多，卖出价小于均线则降低
            factor = ratio - grid_ratio * n
        elif price_low <= price_buy and self.money > 100 * price_buy:
            # 低于网格买入
            self.grid_value = price_buy
            # 均线高于价格 增加偏离值的买入出量
            # 均线低于价格 正常买入
            delta = round((avg - price_buy) / price_buy, 2) if avg > price_buy else 0
            n = 1 + delta * 4  # 设置影响因子 - 卖出价大于均线比例越高则卖出越多，卖出价小于均线则降低
            factor = ratio + grid_ratio * n
        else:
            factor = ratio
        try:
            if factor != ratio:
                factor = 0 if factor < 0 else 100 if factor > 100 else factor  # 买卖超过持仓最大最小值时进行修正
                money_delta = self.money - total_money * (1 - factor / 100)
                count_delta = computed_int_count(money_delta, self.grid_value)
                self.inventory = self.inventory + count_delta
                self.money = self.money - count_delta * self.grid_value

                if self.enable_log:
                    print(json.dumps({
                        'date': date.strftime('%Y%m%d'),
                        'price': self.grid_value,
                        'count_delta': count_delta,
                        'factor': round(factor, 2),
                        'n': round(n, 2),
                        'avg': round(avg, 2),
                    }, ensure_ascii=False))
        except Exception as e:
            print(e)

        total_money = self.total_amount()
        ratio = computed_ratio(self.money, total_money)

        self.z1.append(ratio)
        self.z2.append(self.money)
        self.z3.append(total_money)


symbols = [
    ('沪深300', '000300'),
    ('中证500', '000905'),
    ('中证1000', '000852'),
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
    'symbol': '000905',
    # 'symbol': '000852',
    # 'symbol': 'H20269',
    'start': '20141216',
    'init_money': 100_0000_0000,
    'init_percent': 1,
    'deal_type': 1,  # 按总资产的百分比网格
    # 'deal_type': 5,  # 按总资产百分比做网格，加入超卖超买影响因子 * 1.5 ，越跌越买 使用60周均线
    # 'deal_type': 6,  # 按总资产百分比做网格，加入超卖超买影响因子 * 1.5 ，越跌越买 使用60周均线
    'grid_step': 5,
    'grid_ratio': 10,
}

if __name__ == '__main__':

    # simulate_render(grid_step=11, grid_ratio=27, deal_type=1, symbol='000300')  # 6.46
    # simulate_render(grid_step=14, grid_ratio=22, deal_type=1, symbol='000905')  # 6.6
    # simulate_render(grid_step=12, grid_ratio=27, deal_type=5, symbol='000300')  # 8.15
    # simulate_render(grid_step=14, grid_ratio=29, deal_type=6, symbol='000300')  # 6.89
    # simulate_render(grid_step=13, grid_ratio=13, deal_type=6, symbol='000905')  # 7.37
    simulate_range((5, 20), (10, 30), 1)  # type 4
