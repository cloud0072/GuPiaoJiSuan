import numpy as np
import pandas as pd

import matplotlib.dates as mpd
import matplotlib.pylab as mpl
import matplotlib.pyplot as plt

from src.indexes import example_color

mpl.rcParams['font.sans-serif'] = ['FangSong']
mpl.rcParams['axes.unicode_minus'] = False
plt.switch_backend('TkAgg')


def calc(d1, d2):
    return round((d1 - d2) / d2 * 100, 2)


# 要对比的标的列表
symbol_list = [
    'SH510050',  # 上证50ETF
    # 'SH510300',  # 沪深300
    'SH510500',  # 中证500
    # 'SH512100',  # 中证1000
    # 'SH563300',  # 中证2000ETF
    # 'SH516160',  # 新能源ETF
    # 'SH512890',  # 红利ETF
    # 'SH588000',  # 科创50
    # 'SZ159915',  # 创业板ETF
]


pd.set_option('display.max_rows', None)  # 显示所有行
pd.set_option('display.max_columns', None)  # 显示所有列


# 提取星期几名称
df['weekday'] = df.index.day_name()

# 计算每个工作日的平均涨跌幅
average_change_per_weekday = df.groupby('weekday')['change_percent'].mean()

print(average_change_per_weekday)