import warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ———— 一、屏蔽 Matplotlib 的 Deprecation Warning ————
import matplotlib

warnings.filterwarnings("ignore", category=matplotlib.MatplotlibDeprecationWarning)

# ———— 二、Matplotlib 中文与负号配置 ————
plt.rcParams['font.sans-serif'] = ['SimHei']  # 指定黑体
plt.rcParams['axes.unicode_minus'] = False  # 负号正常显示

# ———— 三、读取数据并预处理 ————
ndx_df = pd.read_csv('^ndx_d.csv', parse_dates=['Date']).sort_values('Date')
gold_df = pd.read_csv('xauusd_d.csv', parse_dates=['Date']).sort_values('Date')

# 归一化收盘价（模拟初始各持1元）
ndx_df['norm_close'] = ndx_df['Close'] / ndx_df['Close'].iloc[0]
gold_df['norm_close'] = gold_df['Close'] / gold_df['Close'].iloc[0]

# 计算日收益率
ndx_df['daily_ret'] = ndx_df['norm_close'].pct_change()
gold_df['daily_ret'] = gold_df['norm_close'].pct_change()

# 合并日收益序列，去除缺失，并以 Date 为索引
returns = (
    pd.merge(
        ndx_df[['Date', 'daily_ret']],
        gold_df[['Date', 'daily_ret']],
        on='Date',
        suffixes=['_ndx', '_gold']
    )
        .dropna()
        .set_index('Date')
)


# ———— 四、绘图函数 ————
def plot_window(sub_returns, window_name):
    weights = np.arange(5, 101, 5)
    ann_factor = 252
    ann_ret_list = []
    ann_var_list = []

    for p in weights:
        w_ndx = p / 100
        comb_ret = w_ndx * sub_returns['daily_ret_ndx'] + (1 - w_ndx) * sub_returns['daily_ret_gold']
        μ = comb_ret.mean()
        ann_ret = (1 + μ) ** ann_factor - 1
        ann_var = comb_ret.var() * ann_factor
        ann_ret_list.append(ann_ret)
        ann_var_list.append(ann_var)

    fig, ax1 = plt.subplots(figsize=(8, 4))
    ax1.plot(weights, ann_ret_list, marker='o', label='年化收益率')
    ax1.set_xlabel('纳指仓位 (%)')
    ax1.set_ylabel('年化收益率')
    ax1.set_title(f'{window_name}：纳指仓位 对比')
    ax1.legend(loc='upper left')
    ax1.set_xlim(0, 100)
    ax1.set_ylim(bottom=0)

    ax2 = ax1.twinx()
    ax2.plot(weights, ann_var_list, linestyle='--', marker='x', label='年化收益方差')
    ax2.set_ylabel('年化收益方差')
    ax2.legend(loc='upper right')
    ax2.set_ylim(bottom=0)

    plt.tight_layout()
    plt.show()


# ———— 五、构建逐年窗口并绘图 ————
years = list(range(2010, 2026))  # 2010 到 2025
windows = [(f'{y}年起', f'{y}-01-01') for y in years]

for window_name, start_date in windows:
    if start_date:
        sub = returns.loc[returns.index >= start_date]
    else:
        sub = returns.copy()

    # 最小方差组合权重计算
    cov_mat = sub.cov().values
    inv_cov = np.linalg.inv(cov_mat)
    ones = np.ones(inv_cov.shape[0])
    w_min = inv_cov.dot(ones) / (ones.dot(inv_cov).dot(ones))
    w_ndx, w_gold = w_min

    # 最小方差组合年化指标
    ret_min = w_ndx * sub['daily_ret_ndx'] + w_gold * sub['daily_ret_gold']
    ann_ret_min = (1 + ret_min.mean()) ** 252 - 1
    ann_var_min = ret_min.var() * 252

    print(f"{window_name} 最小方差组合权重 → 纳指 {w_ndx:.4f}, 黄金 {w_gold:.4f}")
    print(f"  年化收益率：{ann_ret_min:.2%}，年化收益方差：{ann_var_min:.6f}\n")

    # 绘制收益/方差对比图
    plot_window(sub, window_name)
