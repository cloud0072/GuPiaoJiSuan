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
    'SH510300',  # 沪深300
    'SH510500',  # 中证500
    'SH512100',  # 中证1000
    # 'SH563300',  # 中证2000ETF
    # 'SH516160',  # 新能源ETF
    'SH512890',  # 红利ETF
    # 'SH588000',  # 科创50
    # 'SZ159915',  # 创业板ETF
    'SH511010',  # 国债ETF
]

pd.set_option('display.max_rows', None)  # 显示所有行
pd.set_option('display.max_columns', None)  # 显示所有列

year_range = 5  # 时间

# end_date = pd.Timestamp("2021-12-31")
end_date = pd.Timestamp.now()
start_date = end_date - pd.DateOffset(years=year_range)
df_list = []

for symbol in symbol_list:
    df = pd.read_excel(f'../data/download_{symbol}.xlsx')
    df['date'] = pd.to_datetime(df['日期Date'], format='%Y%m%d')
    df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    df.set_index('date', inplace=True)
    df_list.append(pd.DataFrame(df['涨跌幅PRT'], index=df.index))

# 将不同股票的数据合并到一个DataFrame中，以便于处理
combined_df = pd.concat(df_list, axis=1)
combined_df.columns = symbol_list

# 计算每个工作日的平均涨跌幅
average_change_per_weekday_stocks = combined_df.groupby([combined_df.index.day_name()]).mean() \
    .reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])

# # 使用matplotlib绘制图形
# plt.figure(figsize=(14, 8))
#
# for column in average_change_per_weekday_stocks.columns:
#     plt.plot(average_change_per_weekday_stocks.index, average_change_per_weekday_stocks[column], marker='o', label=column)
#
# plt.title('Average Change Percent by Weekday for Multiple Stocks')
# plt.xlabel('Weekday')
# plt.ylabel('Average Change Percent')
# plt.xticks(rotation=45)
# plt.legend(title='Stocks')
# plt.grid(True)
# plt.tight_layout()
# plt.show()

# 使用matplotlib绘制柱状图
fig, ax = plt.subplots(figsize=(14, 8))

width = 0.15  # 柱状图宽度
x = np.arange(len(average_change_per_weekday_stocks.index))  # 柱状图的x坐标

for i, column in enumerate(average_change_per_weekday_stocks.columns):
    ax.bar(x + i * width, average_change_per_weekday_stocks[column], width, label=column)

plt.title('Average Change Percent by Weekday for Multiple Stocks')
plt.xlabel('Weekday')
plt.ylabel('Average Change Percent')
plt.xticks(x + width, ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'))
plt.legend(title='Stocks')
plt.grid(True)
plt.tight_layout()
plt.show()
