import csv
import math
import random

import matplotlib.pyplot as plt
import numpy as np


def test():
    x = range(5)
    y = [3, 1, 1, 3, 4]
    plt.plot(x, y)
    plt.show()


def read(file):
    x = []
    y = []
    avg30 = []
    avg180 = []
    first = 0
    skip = 660
    with open(f'../data/{file}.csv', 'r', encoding='GBK') as f:
        reader = csv.DictReader(f)
        for line in reader:
            skip = skip - 1
            if skip > 0:
                continue
            # print(line)
            # x.append(int(line.get('date')))
            x.append(first)
            first = first + 1
            y.append(float(line.get('收盘Close')))
            if len(y) >= 30:
                avg30.append(np.mean(y[-30:]))
            # else:
            #     avg30.append(0)
            if len(y) >= 180:
                avg180.append(np.mean(y[-180:]))
            # else:
            #     avg180.append(0)

    return x, y, avg30, avg180


def computed_int_count(total, price):
    count = total / price
    return int(count / 100) * 100


def computed_round(start, end):
    return round((end - start) / start * 100, 2)


class Account():

    def __init__(self, config, x, y, avg30, avg180):
        self.x = x  # 序号
        # self.y = [n / 10000 for n in y]  # 指数转换为较小净值
        self.y = y
        self.avg30 = avg30  # 平均值
        self.avg180 = avg180  # 平均值
        self.latest_max = 0  # 最近极大值
        self.latest_min = 0  # 最近极小值
        self.down_stage = True  # 牛市
        self.buy_options = []
        self.sell_options = []

        init_money = config.get('init_money')
        self.init_percent = config.get('init_percent')
        self.step_u = config.get('step_u')
        self.step_d = config.get('step_d')
        self.buy_percent = config.get('buy_percent')
        self.sell_percent = config.get('sell_percent')
        self.buy_count = config.get('buy_count')
        self.sell_count = config.get('sell_count')
        self.deal_type = config.get('deal_type')
        # self.deal_fee = 20  # 交易费用估算，限制频繁交易 20元

        self.base_price = self.y[0]  # 初始基准价格 委托交易成功的价格，作为下一次交易的基准
        self.date = self.x[1]  # 初始日期
        self.inventory = computed_int_count(init_money * self.init_percent, self.base_price)  # 初始持仓数量
        self.money = init_money - self.inventory * self.base_price  # 初始账户余额

        self.z1 = [self.money]  # 历史总余额
        self.z2 = [self.inventory]  # 历史总股数
        self.z3 = [self.total_amount()]  # 历史总资产
        self.z4 = [self.init_percent]  # 历史总资产

    # 总市值 end为查看收盘市值
    def total_amount(self, end=False):
        date = self.date if end else self.date - 1
        return self.money + self.inventory * self.y[date]

    # 股价小于最近极大值且小于avg180)
    # 牛市很难被预测，但可以去回顾。
    # 熊市则可以被记录，也可以被标记为牛熊之间的模糊阶段。
    # def computed_down_stage(self):
    #     price = self.y[self.date]
    #     if self.latest_max <= price:
    #         self.latest_max = price
    #         self.latest_min = price # 刷新低点位置
    #     if self.latest_min > price:
    #         self.latest_min = price
    #     if self.latest_max > price and self.avg180 > price and self.avg30 > price:
    #         self.down_stage = True # 判断为熊市

    def computed_date_next(self):
        end_price = self.y[self.date]  # 获取当天收盘价
        sell_price = self.base_price * self.step_u
        buy_price = self.base_price * self.step_d
        if end_price >= sell_price:
            # 上涨超过基准
            self.deal_with_percent(self.sell_percent, sell_price)
            self.base_price = sell_price
            self.sell_options.append((self.date, sell_price))
        elif end_price <= buy_price:
            # 下跌超过基准
            self.deal_with_percent(self.buy_percent, buy_price)
            self.base_price = buy_price
            self.buy_options.append((self.date, buy_price))

        total_money = self.total_amount()
        self.z1.append(self.money)  # 历史总余额
        self.z2.append(self.inventory)  # 历史总股数
        self.z3.append(total_money)  # 历史总资产
        self.z4.append(round((total_money - self.money) / total_money, 2))  # 持仓比例
        self.date = self.date + 1  # 加一天

    # 通过数量购买或卖出
    def deal_with_count(self, count, price, date):
        total = count * price
        if self.money >= total:
            self.money = self.money - total
            self.inventory = self.inventory + count
        else:
            print('余额不足，购买失败 日期：%s' % date)

    # 智能交易，下一天 （根据均线位置调整买卖额度）
    # 固定交易，下一天 （无论均线位置等额买卖）
    # 通过数量购买或卖出
    def deal_with_percent(self, percent, price):
        date = self.date
        today_price = self.y[date]
        symbol = 1 if percent < 0 else -1
        # avg30 = self.avg30[date - 30] if date >= 30 else today_price
        # delta = pow(1 + (today_price - avg30) / avg30 * symbol, 1)
        avg180 = self.avg180[date - 180] if date >= 180 else today_price
        delta = round(pow(1 + (today_price - avg180) / avg180 * symbol, 1), 4)
        if self.deal_type == '1':
            delta = 1
        percent = percent * delta  # 根据因子修改买卖幅度
        total_amount = self.total_amount()
        count = computed_int_count(percent * total_amount, price)  # 计算买卖数量
        total = count * price  # 计算买卖金额
        if (percent > 0 and self.money >= total) or (percent < 0 and self.inventory + count >= 0):
            self.money = self.money - total
            self.inventory = self.inventory + count
            print('日期：%s 比例：%s 因子：%s 持仓：%s 金额：%s' % (date, round(percent, 4), delta, self.inventory, total_amount))
        elif percent > 0:
            count = computed_int_count(self.money, price)  # 计算买卖数量
            total = count * price  # 计算买卖金额
            self.money = self.money - total
            self.inventory = self.inventory + count
            print('日期：%s 比例：%s 因子：%s 持仓：%s 金额：%s 余额不足，已顶格购买' % (
                date, round(percent, 4), delta, self.inventory, total_amount))
        elif percent < 0:
            count = -self.inventory
            total = count * price  # 计算买卖金额
            self.money = self.money - total
            self.inventory = self.inventory + count
            print('日期：%s 比例：%s 因子：%s 持仓：%s 金额：%s 余券不足，已全部卖出' % (
                date, round(percent, 4), delta, self.inventory, total_amount))


def render3(config):
    file = config.get('init_data')
    x, y, avg30, avg180 = read(file)
    account = Account(config, x, y, avg30, avg180)

    for date in x:
        if date < 1:
            continue
        account.computed_date_next()

    start_total = config.get('init_money')
    end_total = account.total_amount()

    total_per = computed_round(start_total, end_total)
    print('指数增长', computed_round(y[0], y[-1]))
    print('总收益率', total_per)
    print('年化收益率', (total_per / 100 + 1) ** (1 / 10) * 100 - 100)
    print('总收益', end_total)
    # 坐标对齐
    index_max = max(y) * 1.2
    money_max = index_max * account.z3[0] / y[0]
    if max(account.z3) > money_max:
        money_max = max(account.z3) * 1.2
        index_max = money_max * y[0] / account.z3[0]

    # 画图
    fig, ax1 = plt.subplots(1, 1, figsize=(16 * 3, 9), dpi=100)
    ax1.set_ylim(0, index_max)
    ax1.set_xlim(x[0], x[-1])
    ax1.plot(x, y, label="指数", color="red")
    ax1.plot(x, [p * index_max for p in account.z4], label="比例", color="skyblue", linestyle='--', )
    # if config.get('show_avg'):
    # ax1.plot(x[-len(account.avg30):], account.avg30, color="lightgreen", linestyle='--', )
    ax1.plot(x[-len(account.avg180):], account.avg180, color="green", linestyle='--', )

    ax2 = ax1.twinx()
    ax2.plot(x, account.z3, label="总资产", color="blue")
    ax2.set_ylim(0, money_max)
    ax2.set_xlim(x[0], x[-1])

    xs, ys = [list(t) for t in zip(*account.sell_options)]
    xb, yb = [list(t) for t in zip(*account.buy_options)]
    ax1.scatter(xs, ys, marker='o', edgecolor='darkblue', s=30)
    ax1.scatter(xb, yb, marker='o', edgecolor='black', s=30)

    plt.savefig(f'../output/image_{file}.png', bbox_inches='tight')


# 红利低波确实有收益提高，但网格提升幅度太小 不超过5%
config_hldb = {
    'deal_type': '2',
    'init_data': '红利低波',
    'init_money': 100_0000_0000,  # 初始金额 100万
    'init_percent': 1,  # 初始持仓 80%
    'step_u': 1.50,  # 涨x后卖出     5%
    'sell_percent': -0.01,  # 每次卖出占总仓位比重  10%
    'sell_count': 0,  # 每次卖出数量  0
    'step_d': 0.96,  # 跌x后买入    5%
    'buy_percent': 0.04,  # 每次买入占总仓位比重   3%
    'buy_count': 0,  # 每次买入数量   0
}
# render3(config_hldb)

# 网格超额收益确实不小，但总收益太少
config_a500_2 = {  # 120.05
    'deal_type': '2',
    'init_data': 'A500',
    'init_money': 100_0000_0000,  # 初始金额 100万
    'init_percent': 0.9,  # 初始持仓 80%
    'step_u': 1.2,  # 涨x后卖出     5%
    'sell_percent': -0.27,  # 每次卖出占总仓位比重  10%
    'sell_count': 0,  # 每次卖出数量  0
    'step_d': 0.8,  # 跌x后买入    5%
    'buy_percent': 0.30,  # 每次买入占总仓位比重   3%
    'buy_count': 0,  # 每次买入数量   0
}

config_a500_3 = {  # 137.28
    'deal_type': '2',
    'init_data': 'A500',
    'init_money': 100_0000_0000,  # 初始金额 100万
    'init_percent': 0.9,  # 初始持仓 80%
    'step_u': 1.20,  # 涨x后卖出     5%
    'sell_percent': -0.20,  # 每次卖出占总仓位比重  10%
    'sell_count': 0,  # 每次卖出数量  0
    'step_d': 0.8,  # 跌x后买入    5%
    'buy_percent': 0.40,  # 每次买入占总仓位比重   3%
    'buy_count': 0,  # 每次买入数量   0
}

config_a500_4 = {  # 31.0
    'deal_type': '2',
    'init_data': 'A500',
    'init_money': 100_0000_0000,  # 初始金额 100万
    'init_percent': 0.95,  # 初始持仓 80%
    'step_u': 1.2,  # 涨x后卖出     5%
    'sell_percent': -0.3,  # 每次卖出占总仓位比重  10%
    'sell_count': 0,  # 每次卖出数量  0
    'step_d': 0.8,  # 跌x后买入    5%
    'buy_percent': 0.3,  # 每次买入占总仓位比重   3%
    'buy_count': 0,  # 每次买入数量   0
}

config_a500_5 = {  # 31.0
    'deal_type': '2',
    'init_data': 'A500',
    'init_money': 100_0000_0000,  # 初始金额 100万
    'init_percent': 0.9,  # 初始持仓 80%
    'step_u': 1.1,  # 涨x后卖出     5%
    'sell_percent': -0.1,  # 每次卖出占总仓位比重  10%
    'sell_count': 0,  # 每次卖出数量  0
    'step_d': 0.9,  # 跌x后买入    5%
    'buy_percent': 0.1,  # 每次买入占总仓位比重   3%
    'buy_count': 0,  # 每次买入数量   0
}

render3(config_a500_2)

# config_hs300_2 = {
#     'deal_type': '2',
#     'init_data': 'HS300',
#     'init_money': 100_0000_0000,  # 初始金额 100万
#     'init_percent': 0.95,  # 初始持仓 80%
#     'step_u': 1.2,  # 涨x后卖出     5%
#     'sell_percent': -0.3,  # 每次卖出占总仓位比重  10%
#     'sell_count': 0,  # 每次卖出数量  0
#     'step_d': 0.8,  # 跌x后买入    5%
#     'buy_percent': 0.3,  # 每次买入占总仓位比重   3%
#     'buy_count': 0,  # 每次买入数量   0
# }
#
# render3(config_hs300_2)
