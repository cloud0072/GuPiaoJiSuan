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

"""
网格最大的问题就是在涨幅过大的时候无法获得上涨的收益

"""


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


def computed_ratio(money, total):
    return round(money / total * 100, 2)


# 年化收益 每年交易日约等于243天
def computed_annualized(days, series1, series2=[]):
    data_list = []
    if len(series2) == 0:
        series2 = series1
    # series = df['收盘Close']
    for i, row in enumerate(series1):
        if i < days:
            data_list.append(0)
        else:
            oVal = series1.iloc[i - days]
            nVal = series2.iloc[i]
            data_list.append(computed_grow(oVal, nVal))
    return data_list


def read_csindex(codes):
    start = init_config.get('start')
    end = init_config.get('end')
    start_time = pd.to_datetime(start, format=date_format)
    end_time = pd.to_datetime(end, format=date_format) if end else None
    result = []
    for code in codes.split(','):
        df = pd.read_excel(f'../data/download_{code}.xlsx', usecols=['日期Date', '收盘Close', '最高High', '最低Low'])
        df['日期Date'] = pd.to_datetime(df['日期Date'], format=date_format)
        df['180天均线'] = df['收盘Close'].rolling(180).mean()
        df['近一年均线'] = df['收盘Close'].rolling(year_days).mean()
        df = df[df['日期Date'] > start_time]
        if end_time:
            df = df[df['日期Date'] <= end_time]
        df.index = range(1, len(df['日期Date']) + 1)
        result.append(df)
    return result


def simulate_render(grid_step=None, grid_count=None, deal_type=None, symbol=None):
    if grid_step:
        init_config.update({'grid_step': grid_step})
    if grid_count:
        init_config.update({'grid_count': grid_count})
    if deal_type:
        init_config.update({'deal_type': deal_type})
    if symbol:
        init_config.update({'symbol': symbol})
    symbol = init_config.get('symbol')
    [df] = read_csindex(symbol)
    account = Account(init_config, df)
    account.enable_log = True
    account.computed()
    account.render()
    print(json.dumps({
        'grid_step': init_config.get('grid_step'),
        'grid_count': init_config.get('grid_count') * 20000,
        'annual_grow': account.annual_grow(),
        'ratio_avg': round(float(np.mean(account.z1)), 2),
        'index_grow': computed_grow(account.df['收盘Close'].iloc[0], account.df['收盘Close'].iloc[-1]),
        'total_grow': computed_grow(account.z3[0], account.z3[-1]),
    }, ensure_ascii=False))


def simulate_range(conf_step, conf_count, range_step):
    start = init_config.get('start')
    symbol = init_config.get('symbol')
    deal_type = init_config.get('deal_type')
    [df] = read_csindex(symbol)

    symbol_list = []
    grid_step_list = []
    grid_count_list = []
    annual_grow_list = []
    ratio_avg_list = []

    for grid_step in np.arange(conf_step[0], conf_step[1], range_step):
        for grid_count in np.arange(conf_count[0], conf_count[1], range_step):
            grid_step = float(grid_step)
            grid_count = float(grid_count)
            conf = {
                'grid_step': grid_step,
                'grid_count': grid_count,
            }
            init_config.update(conf)
            account = Account(init_config, df)
            account.enable_log = False
            account.computed()
            annual_grow = account.annual_grow()
            ratio_avg = round(float(np.mean(account.z1)), 2)
            symbol_list.append(symbol)
            grid_step_list.append(grid_step)
            grid_count_list.append(grid_count)
            annual_grow_list.append(annual_grow)
            ratio_avg_list.append(ratio_avg)
            print(json.dumps({
                'grid_step': grid_step,
                'grid_count': grid_count * 20000,
                'annual_grow': annual_grow,
                'ratio_avg': ratio_avg,
            }, ensure_ascii=False))

    df = pd.DataFrame({
        'symbol': symbol_list,
        'grid_step': grid_step_list,
        'grid_count': grid_count_list,
        'annual_grow': annual_grow_list,
        'ratio_avg': ratio_avg_list,
    })
    df.to_excel(f'../output/simulate_grid_count_{symbol}_{start}_{deal_type}.xlsx')


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
        self.grid_count = config.get('grid_count', 10)

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
            elif self.deal_type == 2:
                self.computed_avg_next2()
            elif self.deal_type == 3:
                self.computed_avg_next3()
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
        ax1.plot_date(date_index, df['180天均线'], '--', label="180天均线", color="red")
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
        plt.savefig(f'../output/image_grid_count_{self.symbol}_{self.start}_{self.deal_type}.png', bbox_inches='tight')

    """
        网格交易 根据标的最大波动幅度设置网格
        根据均线优化网格
    """

    def computed_avg_next1(self):
        date = self.df['日期Date'].iloc[self.index]
        price_close = self.df['收盘Close'].iloc[self.index]
        price_high = self.df['最高High'].iloc[self.index]
        price_high = price_close if np.isnan(price_high) else price_high
        price_low = self.df['最低Low'].iloc[self.index]
        price_low = price_close if np.isnan(price_low) else price_low
        avg = self.df['180天均线'].iloc[self.index]
        total_money = self.total_amount()
        grid_value = self.grid_value
        grid_step = self.grid_step
        grid_count = self.grid_count * 20000

        ratio = computed_ratio(self.inventory * price_close, total_money)
        price_sell = round(grid_value * (100 + grid_step) / 100, 2)
        price_buy = round(grid_value * (100 - grid_step) / 100, 2)
        count_delta = 0
        if price_sell <= price_high and self.inventory > 0:
            # 大于网格卖出
            # 大于持仓则全部卖出
            count_delta = -grid_count if self.inventory > grid_count else -self.inventory
            if count_delta < 0:
                self.grid_value = price_sell  # 成交价设置为新的网格价
                self.inventory = self.inventory + count_delta
                self.money = self.money - count_delta * price_sell
        elif price_low <= price_buy and ratio < 100:
            # 低于网格买入
            # 大于可买金额则全部买入
            count_delta = grid_count if self.money > grid_count * price_buy \
                else computed_int_count(self.money, price_buy)
            if count_delta > 0:
                self.grid_value = price_buy
                self.inventory = self.inventory + count_delta
                self.money = self.money - count_delta * price_buy

        factor = computed_ratio(self.inventory * price_close, total_money)

        try:
            if self.enable_log and count_delta != 0:
                print(json.dumps({
                    'date': date.strftime('%Y%m%d'),
                    'price': self.grid_value,
                    'count_delta': count_delta,
                    'factor': factor,
                    'avg': round(avg, 2),
                }, ensure_ascii=False))
        except Exception as e:
            print(e)

        total_money = self.total_amount()
        ratio = computed_ratio(self.inventory * price_close, total_money)

        self.z1.append(ratio)
        self.z2.append(self.money)
        self.z3.append(total_money)

    # 仓位越低买的越多
    def computed_avg_next2(self):
        date = self.df['日期Date'].iloc[self.index]
        price_close = self.df['收盘Close'].iloc[self.index]
        price_high = self.df['最高High'].iloc[self.index]
        price_high = price_close if np.isnan(price_high) else price_high
        price_low = self.df['最低Low'].iloc[self.index]
        price_low = price_close if np.isnan(price_low) else price_low
        avg = self.df['180天均线'].iloc[self.index]
        total_money = self.total_amount()
        grid_value = self.grid_value
        grid_step = self.grid_step
        grid_count = self.grid_count * 20000

        ratio = computed_ratio(self.inventory * price_close, total_money)

        price_sell = round(grid_value * (100 + grid_step) / 100, 2)
        price_buy = round(grid_value * (100 - grid_step) / 100, 2)
        count_delta = 0
        if price_sell <= price_high and self.inventory > 0:
            # 大于网格卖出
            # 大于持仓则全部卖出
            grid_count = round(grid_count * (100 + ratio) / 20000, 0) * 100
            count_delta = -grid_count if self.inventory > grid_count else -self.inventory
            if count_delta < 0:
                self.grid_value = price_sell  # 成交价设置为新的网格价
                self.inventory = self.inventory + count_delta
                self.money = self.money - count_delta * price_sell
        elif price_low <= price_buy and ratio < 100:
            # 低于网格买入
            # 大于可买金额则全部买入
            grid_count = round(grid_count * (200 - ratio) / 20000, 0) * 100
            count_delta = grid_count if self.money > grid_count * price_buy \
                else computed_int_count(self.money, price_buy)
            if count_delta > 0:
                self.grid_value = price_buy
                self.inventory = self.inventory + count_delta
                self.money = self.money - count_delta * price_buy

        factor = computed_ratio(self.inventory * price_close, total_money)

        try:
            if self.enable_log and count_delta != 0:
                print(json.dumps({
                    'date': date.strftime('%Y%m%d'),
                    'price': self.grid_value,
                    'count_delta': count_delta,
                    'factor': factor,
                    'avg': round(avg, 2),
                }, ensure_ascii=False))
        except Exception as e:
            print(e)

        total_money = self.total_amount()
        ratio = computed_ratio(self.inventory * price_close, total_money)

        self.z1.append(ratio)
        self.z2.append(self.money)
        self.z3.append(total_money)

    # 按持均线偏离买卖  参考近一年均线
    def computed_avg_next3(self):
        date = self.df['日期Date'].iloc[self.index]
        price_close = self.df['收盘Close'].iloc[self.index]
        price_high = self.df['最高High'].iloc[self.index]
        price_high = price_close if np.isnan(price_high) else price_high
        price_low = self.df['最低Low'].iloc[self.index]
        price_low = price_close if np.isnan(price_low) else price_low
        avg = self.df['近一年均线'].iloc[self.index]
        total_money = self.total_amount()
        grid_value = self.grid_value
        grid_step = self.grid_step
        grid_count = self.grid_count * 20000

        ratio = computed_ratio(self.inventory * price_close, total_money)
        price_sell = round(grid_value * (100 + grid_step) / 100, 2)
        price_buy = round(grid_value * (100 - grid_step) / 100, 2)
        count_delta = 0
        if price_sell <= price_high and self.inventory > 0:
            # 大于网格卖出
            n = round((price_sell - avg) / avg * 2 * grid_count, 2) if price_sell > avg else 0
            grid_count = grid_count + n
            # 大于持仓则全部卖出
            count_delta = -grid_count if self.inventory > grid_count else -self.inventory
            if count_delta < 0:
                self.grid_value = price_sell  # 成交价设置为新的网格价
                self.inventory = self.inventory + count_delta
                self.money = self.money - count_delta * price_sell
        elif price_low <= price_buy and ratio < 100:
            # 低于网格买入
            n = round((avg - price_buy) / avg * 2 * grid_count, 2) if avg > price_buy else 0
            grid_count = grid_count + n
            # 大于可买金额则全部买入
            count_delta = grid_count if self.money > grid_count * price_buy \
                else computed_int_count(self.money, price_buy)
            if count_delta > 0:
                self.grid_value = price_buy
                self.inventory = self.inventory + count_delta
                self.money = self.money - count_delta * price_buy

        factor = computed_ratio(self.inventory * price_close, total_money)

        try:
            if self.enable_log and count_delta != 0:
                print(json.dumps({
                    'date': date.strftime('%Y%m%d'),
                    'price': self.grid_value,
                    'count_delta': count_delta,
                    'factor': factor,
                    'avg': round(avg, 2),
                }, ensure_ascii=False))
        except Exception as e:
            print(e)

        total_money = self.total_amount()
        ratio = computed_ratio(self.inventory * price_close, total_money)

        self.z1.append(ratio)
        self.z2.append(self.money)
        self.z3.append(total_money)


init_config = {
    'start': '20141201',
    'end': '20241201',
    'symbol': '000300',
    # 'symbol': '000905',
    # 'symbol': '000852',
    # 'symbol': 'H20269',
    'init_money': 100_0000_0000,
    'init_percent': 1,
    # 'deal_type': 1,  # 按总资产的百分比网格
    'deal_type': 3,  # 按总资产的百分比网格
    'grid_step': 5,
    'grid_count': 33
}

if __name__ == '__main__':
    # simulate_render(grid_step=10, grid_count=29, deal_type=1, symbol='000300')  # 因子 *5
    # simulate_render(grid_step=12, grid_count=34, deal_type=2, symbol='000300')  # 5.2
    simulate_render(grid_step=5, grid_count=30, deal_type=3, symbol='000300')  # 5.92
    # simulate_range((1, 10), (20, 35), 1)  # type 4
