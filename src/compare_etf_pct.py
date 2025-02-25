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
    # 'SH588000', # 科创50
    # 'SH510300', # 沪深300
    # 'SH510500',  # 中证500
    # 'SH512100', # 中证1000
    # 'SH516160',  # 新能源ETF
    'SH512890',  # 红利ETF
    'SZ159915',  # 创业板ETF
]

year_range = 3  # 时间
date_type = 'W'  # 月度

# 获取当前日期并计算5年前的日期
end_date = pd.Timestamp("2021-12-31")
# end_date = pd.Timestamp.now()
start_date = end_date - pd.DateOffset(years=year_range)
aggs = []

for symbol in symbol_list:
    df = pd.read_excel(f'../data/download_{symbol}.xlsx')
    df['date'] = pd.to_datetime(df['日期Date'], format='%Y%m%d')
    df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
    df.set_index('date', inplace=True)
    # 按月重采样，获取每月第一个交易日的开盘价和最后一个交易日的收盘价
    agg = df.resample(date_type).agg({
        '开盘Open': 'first',
        '收盘Close': 'last'
    })
    # 计算涨跌幅
    agg[f'{symbol}涨幅'] = calc(agg['收盘Close'], agg['开盘Open'])
    aggs.append(agg[[f'{symbol}涨幅']])

merged_df = pd.concat(aggs, axis=1, join='inner')
pd.set_option('display.max_rows', None)  # 显示所有行
pd.set_option('display.max_columns', None)  # 显示所有列

# 打印结果查看
print("月涨跌幅对比:")
print(merged_df)

fig, ax = plt.subplots(figsize=(30, 6))

# 设置柱的位置
x = np.arange(len(merged_df.index))
cols = len(merged_df.columns)
width = round(1 / (1 + cols), 2)

# 绘制柱状图
for i, col in enumerate(merged_df.columns):
    location = x + width * i  # 计算每组柱子相对于中心位置的偏移量
    ax.bar(location, merged_df[col], width, label=col, color=example_color[i])

# 添加一些文本信息
ax.set_xlabel('日期')
ax.set_ylabel('涨跌幅 (%)')
ax.set_title('近5年每月涨跌幅对比')
ax.set_xticks(x)
ax.set_xticklabels(merged_df.index.strftime('%Y-%m-%d'), rotation=45, ha='right')
ax.legend()

# 保存
plt.savefig(f'../output/compare_etf_pct_{start_date.strftime("%Y%m%d")}.png', bbox_inches='tight')
