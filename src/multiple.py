import datetime
import numpy as np
import pandas

import matplotlib.pylab as mpl
mpl.rcParams['font.sans-serif'] = ['FangSong']
mpl.rcParams['axes.unicode_minus'] = False
import matplotlib.pyplot as plt

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


def computed_int_count(total, price):
    count = total / price
    return int(count / 100) * 100


def computed_round(start, end):
    return round((end - start) / start * 100, 2)


class Account():

    def __init__(self, config, dataframe):
        self.df = dataframe
        init_price = self.df['收盘Close'].iloc[0]

        self.init_money = config.get('init_money')
        self.init_percent = config.get('init_percent', 0.8)
        self.inventory = computed_int_count(self.init_money * self.init_percent, init_price)  # 初始持仓数量
        self.money = self.init_money - self.inventory * init_price  # 初始账户余额
        self.loan_inventory = 0
        self.loan_ratio = config.get('loan_ratio', 1.2)
        self.loan_money = self.init_money * self.loan_ratio
        self.index = 0  # 序号
        self.deal_type = config.get('deal_type')
        self.ratio_delta = config.get('ratio_delta', 0.03)
        # self.deal_fee = 20  # 交易费用估算，限制频繁交易 20元

        self.z1 = []  # 历史持仓比例
        self.z2 = []  # 历史总余额
        self.z3 = []  # 历史总资产
        self.z11 = []  # 融资持仓比例
        self.z12 = []  # 融资总余额
        self.z13 = []  # 融资总资产

    # 总市值 end为查看收盘市值
    def total_amount(self):
        return self.money + self.inventory * self.df['收盘Close'].iloc[self.index]

    # 总市值 end为查看收盘市值
    def total_loan(self):
        return self.loan_money + self.loan_inventory * self.df['收盘Close'].iloc[self.index]

    """
        +-3%进行调仓
        最后收益 + 20% 持仓不动的收益 模拟120%的持仓
    """

    def computed_date_next(self):
        price = self.df['收盘Close'].iloc[self.index]  # 获取当天收盘价
        avg = self.df['180天均线'].iloc[self.index]  # 获取当天收盘价
        total_money = self.total_amount()
        ratio = round((total_money - self.money) / total_money, 2)
        # 均线 10% + 则 保持80%仓位
        if 1.10 * avg < price and (ratio > (0.90 + self.ratio_delta) or ratio < (0.90 - self.ratio_delta)):
            factor = 0.90
        # 均线 -10% - 则 保持100%仓位
        elif price <= 1.0 * avg and ratio < (1 - self.ratio_delta):
            factor = 1
        else:
            factor = ratio
        try:
            total_delta = self.money - total_money * (1 - factor)
            count_delta = computed_int_count(total_delta, price)
            self.inventory = self.inventory + count_delta
            self.money = self.money - count_delta * price
        except Exception as e:
            print(e)

        total_money = self.total_amount()
        ratio = round((total_money - self.money) / total_money, 2)

        self.z1.append(ratio)
        self.z2.append(self.money)
        self.z3.append(total_money)

    """
    融资账户
    """

    def computed_loan_next(self):
        price = self.df['收盘Close'].iloc[self.index]  # 获取当天收盘价
        avg = self.df['180天均线'].iloc[self.index]  # 获取当天收盘价
        total_loan = self.total_loan()
        ratio = round((total_loan - self.loan_money) / total_loan, 2)
        # 均线 5% + 则 保持0%仓位
        if 1.05 * avg <= price:
            factor = 0
        # 均线 -10% - 则 保持100%仓位
        elif 0.91 * avg < price <= 0.94 * avg:
            factor = 0.5
        # 均线 -10% - 则 保持100%仓位
        elif price <= 0.88 * avg:
            factor = 1
        else:
            factor = ratio
        try:
            total_delta = self.loan_money - total_loan * (1 - factor)
            count_delta = computed_int_count(total_delta, price)
            self.loan_inventory = self.loan_inventory + count_delta
            self.loan_money = self.loan_money - count_delta * price
            if self.loan_inventory < 1:
                # 将融资赚的钱转到普通账户余额
                init_loan = self.init_money * self.loan_ratio
                pass_money = self.loan_money - init_loan
                self.money = self.money + pass_money
                self.loan_money = init_loan
        except Exception as e:
            print(e)

        total_loan = self.total_loan()
        ratio = round((total_loan - self.loan_money) / total_loan, 2)

        self.z11.append(ratio)
        self.z12.append(self.loan_money)
        self.z13.append(total_loan)


def render_multiple(config):
    start_date = datetime.datetime.strptime('20151028', '%Y%m%d')
    # [hs300df, hl100df] = read(start_date, '000300,H20955,')
    [hlqzdf] = read(start_date, 'H20269')
    # hl100df['180天均线'] = hl100df['收盘Close'].rolling(window=180).mean()
    hlqzdf['180天均线'] = hlqzdf['收盘Close'].rolling(window=180).mean()
    # date300 = pandas.to_datetime(hs300df['日期Date'], format='%Y%m%d')
    # date100 = pandas.to_datetime(hl100df['日期Date'], format='%Y%m%d')
    datehlqz = pandas.to_datetime(hlqzdf['日期Date'], format='%Y%m%d')

    account = Account(config, hlqzdf)
    # 计算
    for d in datehlqz:
        # account.computed_loan_next()
        account.computed_date_next()
        account.index = account.index + 1

    account.index = account.index - 1
    start_total = config.get('init_money')
    end_total = account.total_amount()
    start_loan = account.init_money * account.loan_ratio
    end_loan = account.total_loan()

    total_per = computed_round(start_total, end_total)
    print('指数增长', computed_round(hlqzdf['收盘Close'].iloc[0], hlqzdf['收盘Close'].iloc[-1]))
    print('总收益率', total_per)
    print('年化收益率', (total_per / 100 + 1) ** (1 / 10) * 100 - 100)
    print('总收益', end_total - start_total)
    print('融资总收益', computed_round(start_loan, end_loan))

    # hs300_f = hs300df['收盘Close'].iloc[0]
    # hl100_f = hl100df['收盘Close'].iloc[0]
    hlqz_f = hlqzdf['收盘Close'].iloc[0]

    plt.figure(figsize=(16 * 5, 9))
    plt.plot_date(datehlqz, hlqzdf['收盘Close'], '-', label="H20269", color="red")
    plt.plot_date(datehlqz, hlqzdf['180天均线'], '--', label="180天均线", color="pink")
    plt.plot_date(datehlqz, [(x * 20000) for i, x in enumerate(account.z1)], '--', label="比例", color="skyblue")
    plt.plot_date(datehlqz, [(x / account.z3[0] * hlqz_f) for x in account.z3], '--', label="总资产", color="blue")

    # plt.plot_date(datehlqz, [(x * 0.2 * 20000) for i, x in enumerate(account.z11)], '--', label="loan比例", color="skyblue")
    # plt.plot_date(datehlqz, [(x / account.z13[0] * hlqz_f) for x in account.z13], '--', label="loan总资产", color="blue")

    # plt.plot_date(date300, [(x / hs300_f * hlqz_f) for x in hs300df['收盘Close']], '-', label="000300", color="darkred")
    # plt.plot_date(date100, [(x / hl100_f * hlqz_f) for x in hl100df['收盘Close']], '-', label="H20995", color="orange")

    plt.xlabel('交易日')
    plt.ylabel('收盘价')
    plt.legend(loc='upper right')

    plt.grid(True)
    plt.savefig(f'../output/image_multiple.png', bbox_inches='tight')


config_1 = {
    'init_money': 100_0000_0000,
    'init_percent': 1,
    'loan_ratio': 1.2,
    'deal_type': 1,
    'ratio_delta': 0.03,
}
render_multiple(config_1)
