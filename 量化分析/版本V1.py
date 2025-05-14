import pandas as pd
import numpy as np
from IPython.display import display  # 如果你在 Jupyter Notebook 中使用

# 1. 读取CSV文件
纳指数据 = pd.read_csv('^ndx_d.csv', parse_dates=['Date'])
黄金数据 = pd.read_csv('xauusd_d.csv', parse_dates=['Date'])

# 2. 计算日波动（当日收盘价 - 昨日收盘价）
纳指数据['纳指波动'] = 纳指数据['Close'].diff()
黄金数据['黄金波动'] = 黄金数据['Close'].diff()

# 3. 合并数据并去除缺失值
合并数据 = pd.merge(
    纳指数据[['Date', '纳指波动']],
    黄金数据[['Date', '黄金波动']],
    on='Date'
).dropna().set_index('Date')

# 4. 计算均值和协方差矩阵
日均波动 = 合并数据.mean()
协方差矩阵 = 合并数据.cov()

# 5. 计算最小方差组合权重
协方差矩阵逆 = np.linalg.inv(协方差矩阵.values)
单位向量 = np.ones(len(日均波动))
初始权重 = 协方差矩阵逆.dot(单位向量)
最小方差权重 = 初始权重 / (单位向量.dot(协方差矩阵逆).dot(单位向量))

# 6. 构建输出表格
统计表 = pd.DataFrame({
    '指标': ['日均波动', '日方差'],
    '纳指': [日均波动['纳指波动'], 协方差矩阵.loc['纳指波动', '纳指波动']],
    '黄金': [日均波动['黄金波动'], 协方差矩阵.loc['黄金波动', '黄金波动']]
})

权重表 = pd.DataFrame({
    '资产': ['纳指', '黄金'],
    '最小方差权重': 最小方差权重
})

# 7. 显示结果
display(统计表)
display(权重表)
