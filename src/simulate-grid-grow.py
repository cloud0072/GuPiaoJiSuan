import json
import time
from datetime import datetime, timedelta, date
import numpy as np
import pandas as pd

import matplotlib.pylab as mpl
import matplotlib.pyplot as plt

mpl.rcParams['font.sans-serif'] = ['FangSong']
mpl.rcParams['axes.unicode_minus'] = False

plt.switch_backend('TkAgg')

date_format = '%Y%m%d'
year_days = 244

class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime) or isinstance(obj, date):
            return obj.strftime("%Y%m%d")
        else:
            return json.JSONEncoder.default(self, obj)


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
        df['近两年均线'] = df['收盘Close'].rolling(year_days * 2).mean()
        df = df[df['日期Date'] > start_time]
        if end_time:
            df = df[df['日期Date'] <= end_time]
        df.index = range(1, len(df['日期Date']) + 1)
        result.append(df)
    return result


def simulate_render(symbol=None, deal_type=None, grid_up=None, grid_down=None, ):
    if symbol:
        init_config.update({'symbol': symbol})
    if deal_type:
        init_config.update({'deal_type': deal_type})
    if grid_up:
        init_config.update({
            'grid_up_step': grid_up[0],
            'grid_up_ratio': grid_up[1]
        })
    if grid_down:
        init_config.update({
            'grid_down_step': grid_down[0],
            'grid_down_ratio': grid_down[1]
        })
    symbol = init_config.get('symbol')
    [df] = read_csindex(symbol)
    account = Account(init_config, df)
    account.enable_log = True
    account.computed()
    account.render()
    print(json.dumps({
        'symbol': init_config.get('symbol'),
        'start': init_config.get('start'),
        'end': init_config.get('end'),
        'grid_up_step': grid_up[0],
        'grid_up_ratio': grid_up[1],
        'grid_down_step': grid_down[0],
        'grid_down_ratio': grid_down[1],
        'annual_grow': account.annual_grow(),
        'ratio_avg': round(float(np.mean(account.z1)), 2),
        'index_grow': computed_grow(account.df['收盘Close'].iloc[0], account.df['收盘Close'].iloc[-1]),
        'total_grow': computed_grow(account.z3[0], account.z3[-1]),
    }, ensure_ascii=False))


def simulate_range(symbol, deal_type, conf_date, conf_up_step, conf_up_ratio, conf_down_step, conf_down_ratio,
                   range_step=1):
    date_delta = int(365.25 * 8)
    date_step = 24 * 24 * 60 * 60
    date_start = time.mktime(pd.to_datetime(conf_date[0], format=date_format).timetuple())
    date_end = date_start + date_step * conf_date[1]

    start_list = []
    end_list = []
    symbol_list = []
    grid_up_step_list = []
    grid_up_ratio_list = []
    grid_down_step_list = []
    grid_down_ratio_list = []
    annual_grow_list = []
    ratio_avg_list = []

    for timestamp in np.arange(date_start, date_end, date_step):
        start = datetime.fromtimestamp(timestamp)
        end = start + timedelta(days=date_delta)
        init_config.update({
            'start': start.strftime(date_format),
            'end': end.strftime(date_format),
        })
        [df] = read_csindex(symbol)
        for grid_up_step in np.arange(conf_up_step[0], conf_up_step[1], range_step):
            for grid_up_ratio in np.arange(conf_up_ratio[0], conf_up_ratio[1], range_step):
                for grid_down_step in np.arange(conf_down_step[0], conf_down_step[1], range_step):
                    for grid_down_ratio in np.arange(conf_down_ratio[0], conf_down_ratio[1], range_step):
                        grid_up_step = int(grid_up_step)
                        grid_up_ratio = int(grid_up_ratio)
                        grid_down_step = int(grid_down_step)
                        grid_down_ratio = int(grid_down_ratio)
                        conf = {
                            'grid_up_step': grid_up_step,
                            'grid_up_ratio': grid_up_ratio,
                            'grid_down_step': grid_down_step,
                            'grid_down_ratio': grid_down_ratio,
                        }
                        init_config.update(conf)
                        account = Account(init_config, df)
                        account.enable_log = False
                        account.computed()
                        annual_grow = account.annual_grow()
                        ratio_avg = round(float(np.mean(account.z1)), 2)
                        start_list.append(start)
                        end_list.append(end)
                        symbol_list.append(symbol)
                        grid_up_step_list.append(grid_up_step)
                        grid_up_ratio_list.append(grid_up_ratio)
                        grid_down_step_list.append(grid_down_step)
                        grid_down_ratio_list.append(grid_down_ratio)
                        annual_grow_list.append(annual_grow)
                        ratio_avg_list.append(ratio_avg)
                        print(json.dumps({
                            'symbol': symbol,
                            'start': start,
                            'end': end,
                            'grid_up_step': grid_up_step,
                            'grid_up_ratio': grid_up_ratio,
                            'grid_down_step': grid_down_step,
                            'grid_down_ratio': grid_down_ratio,
                            'annual_grow': annual_grow,
                            'ratio_avg': ratio_avg,
                        }, ensure_ascii=False, cls=DateEncoder))

    df = pd.DataFrame({
        'symbol': symbol_list,
        'start': start_list,
        'end': end_list,
        'grid_up_step': grid_up_step_list,
        'grid_up_ratio': grid_up_ratio_list,
        'grid_down_step': grid_down_step_list,
        'grid_down_ratio': grid_down_ratio_list,
        'annual_grow': annual_grow_list,
        'ratio_avg': ratio_avg_list,
    })
    df.to_excel(f'../output/simulate_grid_grow_{symbol}_{deal_type}.xlsx')


class Account:

    def __init__(self, config, df):
        self.enable_log = False
        self.df = df
        init_price = self.df['收盘Close'].iloc[0]
        init_money = config.get('init_money')
        init_percent = config.get('init_percent', 0.8)
        self.deal_type = config.get('deal_type')
        self.symbol = config.get('symbol')
        self.start = config.get('start')
        self.grid_value = init_price

        self.inventory = computed_int_count(init_money * init_percent, init_price)  # 初始持仓数量
        self.money = init_money - self.inventory * init_price  # 初始账户余额
        # self.loan_inventory = 0
        # self.loan_ratio = config.get('loan_ratio', 1.2)
        # self.loan_money = init_money * self.loan_ratio
        self.index = 0  # 序号

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
            # elif self.deal_type == 2:
            #     self.computed_avg_next2()
            # elif self.deal_type == 5:
            #     self.computed_avg_next5()
            # elif self.deal_type == 6:
            #     self.computed_avg_next6()
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
        # ax1.plot_date(date_index, df['近一年均线'], '--', label="近一年均线", color="red")
        # ax1.plot_date(date_index, df['近两年均线'], '--', label="近两年均线", color="red")
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
        plt.savefig(f'../output/image_grid_grow_{self.symbol}_{self.start}_{self.deal_type}.png', bbox_inches='tight')

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
        grid_up_step = init_config.get('grid_up_step')
        grid_up_ratio = init_config.get('grid_up_ratio')
        grid_down_step = init_config.get('grid_down_step')
        grid_down_ratio = init_config.get('grid_down_ratio')

        ratio = computed_ratio(self.money, total_money)
        price_sell = round(grid_value * (1 + grid_up_step / 100), 2)
        price_buy = round(grid_value * (1 - grid_down_step / 100), 2)
        if price_sell <= price_high:
            # 大于网格卖出
            self.grid_value = price_sell
            factor = ratio - grid_up_ratio
        elif price_low <= price_buy:
            # 低于网格买入
            self.grid_value = price_buy
            factor = ratio + grid_down_ratio
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
    'symbol': '000300',
    # 'symbol': '000905',
    # 'symbol': '000852',
    # 'symbol': 'H20269',
    'start': '20140101',  # 牛市起点
    # 'end': '20150618',  # 牛市结束一周
    'end': '20240101',  # 新起点
    'init_money': 100_0000_0000,
    'init_percent': 1,
    'deal_type': 1,  # 按总资产的百分比网格
    # 'grid_step': 5,
    # 'grid_ratio': 10,
}

if __name__ == '__main__':
    # 探究上涨时怎么做网格
    # simulate_render(grid_step=15, grid_ratio=19, deal_type=1, symbol='000300')  # 10.25
    # simulate_render(grid_step=13, grid_ratio=19, deal_type=2, symbol='000300')  # 9.22
    simulate_range(symbol='000300', deal_type=1, conf_date=('20140101', 1), conf_up_step=(10, 25), conf_up_ratio=(10, 25),
                   conf_down_step=(10, 25), conf_down_ratio=(10, 25))
