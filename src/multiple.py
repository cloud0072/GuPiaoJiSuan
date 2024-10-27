import csv
import datetime

import matplotlib.pylab as mpl
import pandas
from tkinter import *

mpl.rcParams['font.sans-serif'] = ['FangSong']
mpl.rcParams['axes.unicode_minus'] = False
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
plt.switch_backend('TkAgg')


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
    hs300df = pandas.read_excel('../data/download_000300.xlsx')
    hl100df = pandas.read_excel('../data/download_H20955.xlsx')

    x = hs300df[hs300df['日期Date'] > int(start_date.strftime('%Y%m%d'))]
    y = hl100df[hl100df['日期Date'] > int(start_date.strftime('%Y%m%d'))]
    return x, y


def render_multiple():
    start_date = datetime.datetime.strptime('20181231', '%Y%m%d')
    hs300df, hl100df = read(start_date)

    ax1 = plt.subplots(1, 1)
    # fig.autofmt_xdate()
    # ax1.set_ylim(0, max(hs_max, hl_max))
    # ax1.set_xlim(start_date, max(date300[-1], date100[-1]))

    plt.xticks(range(len(hs300df['日期Date'])), hs300df['日期Date'], rotation=30)
    ax1.xaxis.set_major_locator(mdates.DayLocator(bymonthday=range(1, 32), interval=183))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax1.plot(hs300df['日期Date'], hs300df['收盘Close'], '-', label="hs300", color="red")
    ax1.plot(hl100df['日期Date'], [(x / hl100df['收盘Close'][0] * hs300df['收盘Close'][0]) for x in hl100df['收盘Close']], '-', label="hl100", color="darkred")

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
