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
纳指_df = pd.read_csv('^ndx_d.csv', parse_dates=['Date']).sort_values('Date')
黄金_df = pd.read_csv('xauusd_d.csv', parse_dates=['Date']).sort_values('Date')

纳指_df['归一化收盘'] = 纳指_df['Close'] / 纳指_df['Close'].iloc[0]
黄金_df['归一化收盘'] = 黄金_df['Close'] / 黄金_df['Close'].iloc[0]

纳指_df['日收益'] = 纳指_df['归一化收盘'].pct_change()
黄金_df['日收益'] = 黄金_df['归一化收盘'].pct_change()

returns = (
    pd.merge(
        纳指_df[['Date', '日收益']],
        黄金_df[['Date', '日收益']],
        on='Date',
        suffixes=['_ndx', '_gold']
    )
        .dropna()
        .set_index('Date')
)


# ———— 四、绘图函数 ————
def plot_window(sub_returns, window_name):
    权重列表 = np.arange(5, 101, 5)
    年化因子 = 252
    ann_ret_list = []
    ann_var_list = []

    for p in 权重列表:
        w_ndx = p / 100
        comb_ret = w_ndx * sub_returns['日收益_ndx'] + (1 - w_ndx) * sub_returns['日收益_gold']
        μ = comb_ret.mean()
        ann_ret = (1 + μ) ** 年化因子 - 1
        ann_var = comb_ret.var() * 年化因子
        ann_ret_list.append(ann_ret)
        ann_var_list.append(ann_var)

    fig, ax1 = plt.subplots(figsize=(8, 4))

    # 实线：年化收益率
    ax1.plot(权重列表, ann_ret_list, marker='o', label='年化收益率')
    ax1.set_xlabel('纳指仓位 (%)')
    ax1.set_ylabel('年化收益率')
    ax1.set_title(f'{window_name}：纳指仓位 对比')
    ax1.legend(loc='upper left')
    ax1.set_ylim(bottom=0)  # y轴从0开始
    ax1.set_xlim(0, 100)  # x轴从0到100%

    # 虚线：年化收益方差，共享 x 轴
    ax2 = ax1.twinx()
    ax2.plot(权重列表, ann_var_list, linestyle='--', marker='x', label='年化收益方差')
    ax2.set_ylabel('年化收益方差')
    ax2.legend(loc='upper right')
    ax2.set_ylim(bottom=0)  # y轴从0开始

    plt.tight_layout()
    plt.show()


# ———— 五、按窗口计算并绘图 ————
窗口列表 = [
    ('全部', None),
    ('2015年起', '2015-01-01'),
    ('2020年起', '2020-01-01'),
    ('2023年起', '2023-01-01'),
    ('2024年起', '2024-01-01'),
]

for 窗口名, 起始日 in 窗口列表:
    sub = returns.loc[returns.index >= 起始日] if 起始日 else returns.copy()

    cov_mat = sub.cov().values
    inv_cov = np.linalg.inv(cov_mat)
    ones = np.ones(inv_cov.shape[0])
    w_min = inv_cov.dot(ones) / (ones.dot(inv_cov).dot(ones))
    w_ndx, w_gold = w_min

    ret_min = w_ndx * sub['日收益_ndx'] + w_gold * sub['日收益_gold']
    ann_ret_min = (1 + ret_min.mean()) ** 252 - 1
    ann_var_min = ret_min.var() * 252

    print(f"{窗口名} 最小方差组合权重 → 纳指 {w_ndx:.4f}, 黄金 {w_gold:.4f}")
    print(f"  年化收益率：{ann_ret_min:.2%}，年化收益方差：{ann_var_min:.6f}\n")

    plot_window(sub, 窗口名)
