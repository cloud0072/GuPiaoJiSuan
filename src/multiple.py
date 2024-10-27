import csv
import datetime

import matplotlib.pylab as mpl
mpl.rcParams['font.sans-serif'] = ['FangSong']
mpl.rcParams['axes.unicode_minus'] = False
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np


def find_value(array, key, value):
    for item in array:
        if key in item and item[key] == value:
            return item
    return None


def find_x_y(array, key1, key2):
    x = []
    y = []
    for item in array:
        if item.get(key1) and item.get(key2):
            x.append(item.get(key1))
            y.append(item.get(key2))
    return x, y


def read(start_date):
    hq_list = []

    with open(f'../data/HS300.csv', 'r', encoding='GBK') as f:
        reader = csv.DictReader(f)
        for line in reader:
            date = datetime.datetime.strptime(line.get('日期Date'), '%Y%m%d')
            close = float(line.get('收盘Close'))
            if start_date and date >= start_date:
                current = {
                    'date': date,
                    'hs300': close,
                    'hl100': None
                }
                hq_list.append(current)

    with open(f'../data/红利低波.csv', 'r', encoding='GBK') as f:
        reader = csv.DictReader(f)
        for line in reader:
            date = datetime.datetime.strptime(line.get('日期Date'), '%Y%m%d')
            close = float(line.get('收盘Close'))
            if start_date and date >= start_date:
                current = find_value(hq_list, 'date', date)
                if current:
                    current.update({
                        'hl100': close
                    })
                else:
                    hq_list.append({
                        'date': date,
                        'hs300': None,
                        'hl100': close
                    })

    return hq_list


def render_multiple():
    start_date = datetime.datetime.strptime('20141027', '%Y%m%d')
    hq_list = read(start_date)

    date300, hs300 = find_x_y(hq_list, 'date', 'hs300')
    date100, hl100 = find_x_y(hq_list, 'date', 'hl100')

    fig, ax1 = plt.subplots(1, 1, figsize=(16 * 3, 9), dpi=100)
    # fig.autofmt_xdate()
    # ax1.set_ylim(0, max(hs_max, hl_max))
    # ax1.set_xlim(start_date, max(date300[-1], date100[-1]))

    plt.xticks(range(len(date300)), date300, rotation=30)
    ax1.xaxis.set_major_locator(mdates.DayLocator(bymonthday=range(1,32), interval=30))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax1.plot(date300, hs300, '-', label="hs300", color="red")
    ax1.plot(date100, [(x / hl100[0] * hs300[0]) for x in hl100], '-', label="hl100", color="darkred")

    ax1.set_xlabel('交易日')
    ax1.set_ylabel('收盘价')
    ax1.legend(loc='upper right')

    # ax2 = ax1.twinx()
    # ax2.plot(x, account.z3, label="总资产", color="blue")
    # ax2.set_ylim(0, money_max)
    # ax2.set_xlim(x[0], x[-1])

    # plt.legend(('HS300', 'HL100'))
    # plt.grid(True)
    plt.savefig(f'../output/image_multiple.png', bbox_inches='tight')


render_multiple()