import warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ———— 一、屏蔽 Matplotlib 的 Deprecation Warning ————
import matplotlib
warnings.filterwarnings("ignore", category=matplotlib.MatplotlibDeprecationWarning)

# ———— 二、Matplotlib 中文与负号配置 ————
plt.rcParams['font.sans-serif'] = ['SimHei']       # 指定黑体
plt.rcParams['axes.unicode_minus'] = False         # 负号正常显示

# ———— 三、读取多资产数据 ————
def load_asset(file, name):
    df = pd.read_csv(file, parse_dates=['Date'])
    df = df.sort_values('Date')
    df = df[['Date', 'Close']].rename(columns={'Close': name})
    return df

资产配置 = {
    '恒生科技': ('恒生科技.csv', 80000),
    '纳指100': ('纳斯达克100.csv', 80000),
    '红利低波': ('红利低波ETF.csv', 150000),
    '消费50': ('消费50ETF.csv', 100000),
    '伦敦金': ('xauusd_d.csv', 80000)
}

dfs = []
for 名称, (路径, 金额) in 资产配置.items():
    df = load_asset(路径, 名称)
    dfs.append(df)

# 合并所有数据
数据 = dfs[0]
for df in dfs[1:]:
    数据 = pd.merge(数据, df, on='Date', how='inner')

# 仅保留2021年1月1日及之后的数据
数据 = 数据[数据['Date'] >= '2021-01-01'].copy()
数据.set_index('Date', inplace=True)

# ———— 四、计算净值走势 ————
初始净值 = {}
for 名称 in 资产配置:
    初始净值[名称] = 数据[名称].iloc[0]

总金额 = sum(v for _, v in 资产配置.values())

净值 = pd.Series(dtype=float)
组合走势 = pd.Series(dtype=float)

for 日期, 行 in 数据.iterrows():
    总市值 = 0
    for 名称, (_, 投入) in 资产配置.items():
        当前价 = 行[名称]
        初始价 = 初始净值[名称]
        当前市值 = 投入 * (当前价 / 初始价)
        总市值 += 当前市值
    组合走势.at[日期] = 总市值 / 总金额  # 归一化为净值

# ———— 五、绘制组合净值曲线 ————
plt.figure(figsize=(10, 5))
plt.plot(组合走势, label='组合净值')
plt.title('自 2021 年起组合净值回测')
plt.xlabel('日期')
plt.ylabel('净值')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()

# ———— 六、绘制各资产独立净值走势 ————
plt.figure(figsize=(12, 6))
for 名称 in 资产配置:
    初始价 = 初始净值[名称]
    单项净值 = 数据[名称] / 初始价
    plt.plot(数据.index, 单项净值, label=名称)

plt.title('各资产自 2021 年起独立净值走势')
plt.xlabel('日期')
plt.ylabel('净值')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()