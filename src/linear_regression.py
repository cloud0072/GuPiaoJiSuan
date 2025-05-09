import numpy as np
import pandas as pd
import matplotlib.pylab as mpl
import matplotlib.pyplot as plt

mpl.rcParams['font.sans-serif'] = ['FangSong']
mpl.rcParams['axes.unicode_minus'] = False
plt.switch_backend('TkAgg')


def calc_data():
    resample_type = 'ME'
    # resample_type = 'QE'
    # resample_type = 'YE'
    # name = 'SH000001'
    # name = 'SH000300'
    name = 'SH510300'
    # 多项式回归，最高次幂
    deg = 2
    # 读取Excel文件
    # datasource = pd.read_excel('../data/download_SH510300.xlsx')
    datasource = pd.read_excel(f'../data/download_{name}.xlsx')

    # 确保日期列被正确解析为日期时间类型
    datasource['日期Date'] = pd.to_datetime(datasource['日期Date'], format='%Y%m%d')

    # 设置日期为索引
    datasource.set_index('日期Date', inplace=True)

    # 按月重采样数据，并计算每月的最低价
    df = datasource['最低Low'].resample(resample_type).min().to_frame(name='value')
    df['x'] = [i for i, value in enumerate(df.values)]

    # 使用numpy进行线性拟合
    coefficients = np.polyfit(df['x'], df['value'], deg)
    poly = np.poly1d(coefficients)

    # 计算拟合后的价格值
    df['fit_price'] = poly(df['x'])

    # 绘图
    plt.figure(figsize=(14, 7))
    plt.plot(df.index, df['value'], '.', label=f'原始数据{name}_{resample_type}低点')  # 散点图：原始数据
    plt.plot(df.index, df['fit_price'], 'r-',  label=f'拟合曲线: y = {coefficients[0]:.4f}x^2 + {coefficients[1]:.4f}x + {coefficients[2]:.4f}')  # 拟合曲线

    # 添加标题和标签
    plt.title('价格随时间变化及线性回归拟合')
    plt.xlabel('日期')
    plt.ylabel('价格')
    # 显示图例
    plt.legend()
    # 显示网格
    plt.grid(True)
    # plt.show()
    plt.savefig(f'../output/linear_regression_{resample_type}.png', bbox_inches='tight')


calc_data()