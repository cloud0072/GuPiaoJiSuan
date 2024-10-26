import csv

import matplotlib.pyplot as plt
import numpy


def test():
    x = range(5)
    y = [3, 1, 1, 3, 4]
    plt.plot(x, y)
    plt.show()


def read():
    x = []
    y = []
    first = 0
    with open('../data/红利低波.csv', 'r', encoding='utf8') as f:
        reader = csv.DictReader(f)
        for line in reader:
            # print(line)
            # x.append(int(line.get('date')))
            x.append(first)
            first = first + 1
            y.append(float(line.get('value')))
    return x, y


def render():
    x, y = read()
    plt.figure(figsize=(16 * 5, 9), dpi=100)
    plt.plot(x, y)
    # plt.show()
    plt.savefig('../output/image.png', bbox_inches='tight')


# render()


def computed_int_count(total, price):
    count = total / price
    return int(count / 100) * 100


class Account():

    def __init__(self, config, x, y):
        self.x = x
        self.y = [n / 10000 for n in y]  # 指数转换为较小净值

        init_money = config.get('init_money')
        self.init_percent = config.get('init_percent')
        self.step_u = config.get('step_u')
        self.step_d = config.get('step_d')
        self.buy_percent = config.get('buy_percent')
        self.sell_percent = config.get('sell_percent')
        self.buy_count = config.get('buy_count')
        self.sell_count = config.get('sell_count')
        # self.deal_fee = 20  # 交易费用估算，限制频繁交易 20元

        self.base_price = self.y[0]  # 初始基准价格 委托交易成功的价格，作为下一次交易的基准
        self.date = self.x[1]  # 初始日期
        self.inventory = computed_int_count(init_money * self.init_percent, self.base_price)  # 初始持仓数量
        self.money = init_money - self.inventory * self.base_price  # 初始账户余额

        self.z1 = [self.money]  # 历史总余额
        self.z2 = [self.inventory]  # 历史总股数
        self.z3 = [self.total_amount()]  # 历史总资产

    # 总市值 end为查看收盘市值
    def total_amount(self, end=False):
        date = self.date if end else self.date - 1
        return self.money + self.inventory * self.y[date]

    # 通过数量购买或卖出
    def deal_with_count(self, count, price, date):
        total = count * price
        if self.money >= total:
            self.money = self.money - total
            self.inventory = self.inventory + count
        else:
            print('余额不足，购买失败 日期：%s' % date)

    # 通过数量购买或卖出
    def deal_with_percent(self, percent, price, date):
        count = computed_int_count(percent * self.total_amount(), price)  # 计算买卖数量
        total = count * price  # 计算买卖金额
        if (count > 0 and self.money >= total) or (count < 0 and self.inventory >= count):
            self.money = self.money - total
            self.inventory = self.inventory + count
            print('日期：%s 金额：%s' % (date, total))
        else:
            print('日期：%s 余额不足，购买失败 ' % date)

    # 下一天交易
    def computed_date_next(self, date):
        # date = self.date
        base_price = self.base_price
        start_price = self.y[date - 1]  # 开盘价是上一天的收盘价
        end_price = self.y[date]  # 获取当天收盘价
        sell_price = self.base_price * self.step_u
        buy_price = self.base_price * self.step_d
        if end_price >= sell_price:
            # 上涨超过基准
            self.deal_with_percent(self.sell_percent, sell_price, date)
            self.base_price = sell_price
        elif end_price <= buy_price:
            # 下跌超过基准
            self.deal_with_percent(self.buy_percent, buy_price, date)
            self.base_price = buy_price

        self.z1.append(self.money)  # 历史总余额
        self.z2.append(self.inventory)  # 历史总股数
        self.z3.append(self.total_amount())  # 历史总资产
        self.date = date + 1  # 加一天


init_config = {
    'init_money': 100_0000,  # 初始金额 100万
    'init_percent': 0.9,  # 初始持仓 80%
    'step_u': 1.02,  # 涨x后卖出     5%
    'step_d': 0.98,  # 跌x后买入    5%
    'buy_percent': 0.02,  # 每次买入占总仓位比重   11%
    'sell_percent': -0.01,  # 每次卖出占总仓位比重  10%
    'buy_count': 0,  # 每次买入数量   0
    'sell_count': 0,  # 每次卖出数量  0
}


def render2():
    x, y = read()
    account = Account(init_config, x, y)

    for date in x:
        if date < 2:
            continue
        account.computed_date_next(date)

    plt.figure(figsize=(16 * 5, 9), dpi=100)
    plt.plot(x, y, label="指数", color="red")
    plt.plot(x, account.z1, label="余额", color="green")
    plt.plot(x, account.z2, label="股数", color="blue")
    plt.plot(x, account.z3, label="总资产", color="gray")
    # plt.show()
    plt.savefig('../output/image.png', bbox_inches='tight')
    print('total', account.total_amount())


render2()
