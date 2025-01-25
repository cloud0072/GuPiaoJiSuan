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
        df = pd.read_excel(f'../data/download_{code}.xlsx', usecols=['日期Date', '收盘Close'])
        df['日期Date'] = pd.to_datetime(df['日期Date'], format=date_format)
        df['近5日均线'] = df['收盘Close'].rolling(5).mean()
        df['180天均线'] = df['收盘Close'].rolling(180).mean()
        df['近6月收益率'] = computed_annualized(int(year_days / 2), df['收盘Close'])
        df['近一年收益率'] = computed_annualized(year_days, df['收盘Close'], )
        df['近5日均线收益率'] = computed_annualized(year_days, df['近5日均线'], df['收盘Close'])
        # df['近两年收益率'] = computed_annualized(df['收盘Close'], year_days * 2)
        df = df[df['日期Date'] > start_time]
        if end_time:
            df = df[df['日期Date'] <= end_time]
        df.index = range(1, len(df['日期Date']) + 1)
        result.append(df)
    return result


def read_snowball(codes):
    start = init_config.get('start')
    end = init_config.get('end')
    start_time = pd.to_datetime(start, format=date_format)
    end_time = pd.to_datetime(end, format=date_format) if end else None
    result = []
    for code in codes.split(','):
        df = pd.read_excel(f'../data/download_SH{code}.xlsx', usecols=['日期Date', '收盘Close'])
        df['日期Date'] = pd.to_datetime(df['日期Date'], format=date_format)
        df['近5日均线'] = df['收盘Close'].rolling(7).mean()
        df['180天均线'] = df['收盘Close'].rolling(180).mean()
        df['近6月收益率'] = computed_annualized(int(year_days / 2), df['收盘Close'])
        df['近6月5日均线收益率'] = computed_annualized(int(year_days / 2), df['近5日均线'], df['收盘Close'])
        df['近一年收益率'] = computed_annualized(year_days, df['收盘Close'], )
        df['近5日均线收益率'] = computed_annualized(year_days, df['近5日均线'], df['收盘Close'])
        # df['近两年收益率'] = computed_annualized(year_days * 2, df['收盘Close'], )
        df = df[df['日期Date'] > start_time]
        if end_time:
            df = df[df['日期Date'] <= end_time]
        df.index = range(1, len(df['日期Date']) + 1)
        result.append(df)
    return result


def simulate_render(**args):
    if 'symbol' in args:
        init_config.update({'symbol': args.get('symbol')})
    if 'deal_type' in args:
        init_config.update({'deal_type': args.get('deal_type')})
    if 'annual_sell' in args:
        init_config.update({'annual_sell': args.get('annual_sell')})
    if 'annual_buy' in args:
        init_config.update({'annual_buy': args.get('annual_buy')})
    if 'hs300_ratio' in args:
        init_config.update({'hs300_ratio': args.get('hs300_ratio')})
    start = init_config.get('start')
    symbol = init_config.get('symbol')
    data_source = init_config.get('data_source')
    [df] = read_snowball(symbol) if data_source == 'snowball' else read_csindex(symbol)
    [hs300df] = read_snowball('000300')
    account = Account(init_config, df, hs300df)
    account.enable_log = True
    account.computed()
    account.render()
    ratio_avg = round(float(np.mean(account.z1)), 2)
    print(json.dumps({
        'annual_sell': init_config.get('annual_sell'),
        'annual_buy': init_config.get('annual_buy'),
        'annual_grow': account.annual_grow(),
        'ratio_avg': ratio_avg,
    }, ensure_ascii=False))


def simulate_range(conf_annual_sell, conf_annual_buy, range_step=1):
    start = init_config.get('start')
    symbol = init_config.get('symbol')
    deal_type = init_config.get('deal_type')
    data_source = init_config.get('data_source')

    [df] = read_snowball(symbol) if data_source == 'snowball' else read_csindex(symbol)
    [hs300df] = read_snowball('000300')

    # -18 ~ 28%
    start_list = []
    symbol_list = []
    annual_sell_list = []
    annual_buy_list = []
    annual_grow_list = []
    ratio_avg_list = []
    for annual_sell in np.arange(conf_annual_sell[0], conf_annual_sell[1], range_step):
        for annual_buy in np.arange(conf_annual_buy[0], min(conf_annual_buy[1], annual_sell + 1), range_step):
            # hs300_ratio = round(temp * 0.05, 2)
            init_config.update({
                'annual_sell': float(annual_sell),
                'annual_buy': float(annual_buy),
            })
            account = Account(init_config, df, hs300df)
            account.computed()
            annual_grow = account.annual_grow()
            ratio_avg = round(float(np.mean(account.z1)), 2)
            symbol_list.append(symbol)
            start_list.append(start)
            annual_sell_list.append(annual_sell)
            annual_buy_list.append(annual_buy)
            annual_grow_list.append(annual_grow)
            ratio_avg_list.append(ratio_avg)
            print(json.dumps({
                'annual_sell': float(annual_sell),
                'annual_buy': float(annual_buy),
                'annual_grow': annual_grow,
                'ratio_avg': ratio_avg,
            }, ensure_ascii=False))

    df = pd.DataFrame({
        'symbol': symbol_list,
        'start': start_list,
        'annual_sell': annual_sell_list,
        'annual_buy': annual_buy_list,
        'annual_grow': annual_grow_list,
        'ratio_avg': ratio_avg_list,
    })
    df.to_excel(f'../output/simulate_{symbol}_{start}_{deal_type}.xlsx')


class Account:

    def __init__(self, config, df, hs300df):
        self.enable_log = False
        self.df = df
        self.hs300df = hs300df
        init_price = self.df['收盘Close'].iloc[0]
        init_money = config.get('init_money')
        init_percent = config.get('init_percent', 1)
        self.symbol = config.get('symbol')
        self.start = config.get('start')
        self.annual_sell = config.get('annual_sell', 12)
        self.annual_buy = config.get('annual_buy', 10)

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

    def render(self):
        df = self.df
        hs300df = self.hs300df
        date_index = df['日期Date']
        amount_factor = df['收盘Close'].iloc[0] / self.z3[0]
        hs300_factor = df['收盘Close'].iloc[0] / hs300df['收盘Close'].iloc[0]

        fig, ax1 = plt.subplots(figsize=(4 * 10, 4))
        ax1.plot_date(date_index, df['收盘Close'], '-', label=self.symbol, color="red")
        # ax1.plot_date(hs300df['日期Date'], [(x * hs300_factor) for x in hs300df['收盘Close']], '-', label='000300', color="orange")
        # ax1.plot_date(date_index, df['180天均线'], '--', label="180天均线", color="pink")
        ax1.plot_date(date_index, [x * amount_factor for x in self.z3], '-', label="总资产", color="darkred")

        ax2 = ax1.twinx()
        avg_6m = df['近6月收益率'].mean()
        avg_year = df['近一年收益率'].mean()
        # avg_2year = df['近两年收益率'].mean()

        ax2.plot_date(hs300df['日期Date'], hs300df['近一年收益率'], '-', label='000300', color="orange")
        # ax2.plot_date(date_index, df['近6月收益率'], '--', label="近6月收益率", color="skyblue")
        # ax2.plot_date(date_index, [avg_6m for d in date_index], '--', label="平均收益率", color="skyblue")
        # ax2.plot_date(date_index, df['近一年收益率'], '--', label="近一年收益率", color="skyblue")
        ax2.plot_date(date_index, df['近6月5日均线收益率'], '--', label="近6月5日均线收益率", color="skyblue")
        # ax2.plot_date(date_index, [avg_year for d in date_index], '--', label="平均收益率", color="skyblue")
        # ax2.plot_date(date_index, df['近两年收益率'], '--', label="近两年收益率", color="blue")
        # ax2.plot_date(date_index, [avg_2year for d in date_index], '--', label="平均收益率", color="blue")
        ax2.plot_date(date_index, self.z1, '--', label="比例", color="darkblue")

        # ax.xlabel('交易日')
        # ax.ylabel('收盘价')
        # ax.legend(loc='upper right')
        # ax.xaxis.set_major_locator(mdates.DayLocator())

        ax1.grid(True)
        plt.savefig(f'../output/image_hongli_{self.symbol}_{self.start}_{self.deal_type}.png', bbox_inches='tight')


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
                self.computed_annual_next1()
            elif self.deal_type == 2:
                self.computed_annual_next2()
            elif self.deal_type == 3:
                self.computed_annual_next3()
            elif self.deal_type == 4:
                self.computed_annual_next4()
            else:
                raise SystemError('未找到合适的策略')
            self.index = self.index + 1
        self.index = self.index - 1

    # 根据近一年涨幅作为买卖参考
    # 有时会出现高买低买的问题
    def computed_annual_next1(self):
        date = self.df['日期Date'].iloc[self.index]
        price = self.df['收盘Close'].iloc[self.index]  # 获取当天收盘价
        annual = self.df['近一年收益率'].iloc[self.index]
        total_money = self.total_amount()
        annual_sell = self.annual_sell
        annual_buy = self.annual_buy

        ratio = computed_ratio(self.money, total_money)
        if annual <= annual_buy:
            factor = 100
        elif annual_sell < annual:
            factor = 0
        else:
            factor = ratio
        try:
            factor = 0 if factor < 0 else 100 if factor > 100 else factor  # 买卖超过持仓最大最小值时进行修正
            money_delta = self.money - total_money * (1 - factor / 100)
            count_delta = computed_int_count(money_delta, price)
            self.inventory = self.inventory + count_delta
            self.money = self.money - count_delta * price

            if self.enable_log and count_delta != 0:
                print(json.dumps({
                    'date': date.strftime('%Y%m%d'),
                    'price': price,
                    'count_delta': count_delta,
                    'factor': factor,
                    'annual': annual,
                }, ensure_ascii=False))
        except Exception as e:
            print(e)

        total_money = self.total_amount()
        ratio = computed_ratio(self.money, total_money)

        self.z1.append(ratio)
        self.z2.append(self.money)
        self.z3.append(total_money)

    def computed_annual_next2(self):
        date = self.df['日期Date'].iloc[self.index]
        price = self.df['收盘Close'].iloc[self.index]  # 获取当天收盘价
        annual = self.df['近6月收益率'].iloc[self.index]
        total_money = self.total_amount()
        annual_sell = self.annual_sell
        annual_buy = self.annual_buy

        ratio = computed_ratio(self.money, total_money)
        if annual <= annual_buy:
            factor = 100
        elif annual_sell < annual:
            factor = 0
        else:
            factor = ratio
        try:
            factor = 0 if factor < 0 else 100 if factor > 100 else factor  # 买卖超过持仓最大最小值时进行修正
            money_delta = self.money - total_money * (1 - factor / 100)
            count_delta = computed_int_count(money_delta, price)
            self.inventory = self.inventory + count_delta
            self.money = self.money - count_delta * price

            if self.enable_log and count_delta != 0:
                print(json.dumps({
                    'date': date.strftime('%Y%m%d'),
                    'price': price,
                    'count_delta': count_delta,
                    'factor': factor,
                    'annual_6m': annual,
                }, ensure_ascii=False))
        except Exception as e:
            print(e)

        total_money = self.total_amount()
        ratio = computed_ratio(self.money, total_money)

        self.z1.append(ratio)
        self.z2.append(self.money)
        self.z3.append(total_money)

    # 使用均线收益率，平滑收益
    def computed_annual_next3(self):
        date = self.df['日期Date'].iloc[self.index]
        price = self.df['收盘Close'].iloc[self.index]  # 获取当天收盘价
        annual = self.df['近5日均线收益率'].iloc[self.index]
        total_money = self.total_amount()
        annual_sell = self.annual_sell
        annual_buy = self.annual_buy

        ratio = computed_ratio(self.money, total_money)
        if annual <= annual_buy:
            factor = 100
        elif annual_sell < annual:
            factor = 0
        else:
            factor = ratio
        try:
            factor = 0 if factor < 0 else 100 if factor > 100 else factor  # 买卖超过持仓最大最小值时进行修正
            money_delta = self.money - total_money * (1 - factor / 100)
            count_delta = computed_int_count(money_delta, price)
            self.inventory = self.inventory + count_delta
            self.money = self.money - count_delta * price

            if self.enable_log and count_delta != 0:
                print(json.dumps({
                    'date': date.strftime('%Y%m%d'),
                    'price': price,
                    'count_delta': count_delta,
                    'factor': factor,
                    'annual_6m': annual,
                }, ensure_ascii=False))
        except Exception as e:
            print(e)

        total_money = self.total_amount()
        ratio = computed_ratio(self.money, total_money)

        self.z1.append(ratio)
        self.z2.append(self.money)
        self.z3.append(total_money)

    # 加入沪深三百近一年涨幅作为影响因子
    def computed_annual_next4(self):
        date = self.df['日期Date'].iloc[self.index]
        price = self.df['收盘Close'].iloc[self.index]  # 获取当天收盘价
        annual = self.df['近6月5日均线收益率'].iloc[self.index]
        annual_300 = self.hs300df['近6月收益率'].iloc[self.index]
        total_money = self.total_amount()
        # 控制因子不超过前值的20% 约2 则
        hs300_factor = annual_300 * init_config.get('hs300_ratio')
        hs300_factor = -10 if hs300_factor < -10 else 100 if hs300_factor > 100 else hs300_factor
        annual_sell = self.annual_sell + hs300_factor
        annual_buy = self.annual_buy + hs300_factor

        ratio = computed_ratio(self.money, total_money)
        if annual <= annual_buy:
            factor = 100
        elif annual_sell < annual:
            factor = 0
        else:
            factor = ratio
        try:
            factor = 0 if factor < 0 else 100 if factor > 100 else factor  # 买卖超过持仓最大最小值时进行修正
            money_delta = self.money - total_money * (1 - factor / 100)
            count_delta = computed_int_count(money_delta, price)
            self.inventory = self.inventory + count_delta
            self.money = self.money - count_delta * price

            if self.enable_log and count_delta != 0:
                print(json.dumps({
                    'date': date.strftime('%Y%m%d'),
                    'price': price,
                    'count_delta': count_delta,
                    'factor': factor,
                    'hs300_factor': round(hs300_factor, 2),
                    'annual': annual,
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
]
etfs = [
    # ('中证红利ETF', '515080'),
    ('上证50ETF', '510050'),
    ('红利低波100ETF', '515100'),
    ('红利低波ETF', '512890'),
]
init_config = {
    # 'symbol': '000905',
    # 'symbol': '000300',
    # 'symbol': 'H20269',
    # 'symbol': 'H20955',
    # 'symbol': '515080',
    'symbol': '510050',
    'start': '20140101',
    # 'start': '20191201',
    # 'end': '20191201',
    'end': '20250101',
    'init_money': 100_0000_0000,
    'init_percent': 1,
    # 'data_source': 'csindex',
    'data_source': 'snowball',
    'deal_type': 1,  # 年化收益 上下买入卖出
    # 'deal_type': 2,  # 6个月收益
    # 'deal_type': 3,  # 近一年 30天均线收益
    # 'deal_type': 4,  # 6个月收益 带沪深300涨幅因子
    'annual_sell': 12,
    'annual_buy': 10,
    'hs300_ratio': 2  # 30 -> 2 神奇！和hs300收益率有负的相关性
}

if __name__ == '__main__':
    # 19-24 / 14-24
    # simulate_render(deal_type=1, annual_sell=19, annual_buy=9)  # 年化 26.35/13.43 持仓时长67
    # simulate_render(deal_type=1, annual_sell=17, annual_buy=9)  # 年化 26.03/13.13 持仓时长63.4
    # simulate_render(deal_type=2, annual_sell=19, annual_buy=-3)  # 年化 25.95/14.28 持仓时长68
    # simulate_render(deal_type=3, annual_sell=18, annual_buy=7)  # 年化 28.01/14.34 持仓时长70.7
    # simulate_render(deal_type=4, annual_sell=19, annual_buy=7, hs300_ratio=-0.05)  # 年化 32.02/16.02 持仓时长56.24
    # simulate_range((12, 25), (0, 20), 1)

    # 14-19
    # simulate_render(deal_type=4, annual_sell=20, annual_buy=-5, hs300_ratio=0.1)  # 年化 7.26 持仓时长51.64
    # simulate_render(deal_type=4, annual_sell=20, annual_buy=10, hs300_ratio=3)  # 年化 7.26 持仓时长51.64
    # simulate_range((80, 90), (0, 10), 1)

    # 15-25
    # simulate_render(deal_type=1, annual_sell=-3, annual_buy=-6, hs300_ratio=2)  # 510050 年化 5.58 持仓时长34.43
    simulate_range((-5, 10), (-10, 0), 1)

