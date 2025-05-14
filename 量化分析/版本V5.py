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

# ———— 三、读取数据并预处理 ————
ndx_df = pd.read_csv('^ndx_d.csv', parse_dates=['Date']).sort_values('Date')
gold_df = pd.read_csv('xauusd_d.csv', parse_dates=['Date']).sort_values('Date')

ndx_df['norm_close'] = ndx_df['Close'] / ndx_df['Close'].iloc[0]
gold_df['norm_close'] = gold_df['Close'] / gold_df['Close'].iloc[0]

ndx_df['daily_ret'] = ndx_df['norm_close'].pct_change()
gold_df['daily_ret'] = gold_df['norm_close'].pct_change()

returns = (
    pd.merge(
        ndx_df[['Date','daily_ret']],
        gold_df[['Date','daily_ret']],
        on='Date',
        suffixes=['_ndx','_gold']
    )
    .dropna()
    .set_index('Date')
)

# ———— 四、绘图函数 ————
def plot_window(sub_returns, window_name):
    weights = np.arange(2, 101, 2)
    ann_factor = 252
    ann_ret_list = []
    ann_var_list = []
    ann_rr_list = []  # 单位风险收益

    for p in weights:
        w_ndx = p / 100
        comb_ret = w_ndx * sub_returns['daily_ret_ndx'] + (1 - w_ndx) * sub_returns['daily_ret_gold']
        μ = comb_ret.mean()
        ann_ret = (1 + μ)**ann_factor - 1
        ann_var = comb_ret.var() * ann_factor
        ann_ret_list.append(ann_ret)
        ann_var_list.append(ann_var)
        ann_rr_list.append(ann_ret / ann_var if ann_var > 0 else np.nan)

    # 找出最大 & 最小单位风险收益
    max_idx = np.nanargmax(ann_rr_list)
    min_idx = np.nanargmin(ann_rr_list)
    max_w, min_w = weights[max_idx], weights[min_idx]
    max_rr, min_rr = ann_rr_list[max_idx], ann_rr_list[min_idx]

    fig, ax1 = plt.subplots(figsize=(8, 4))
    l1, = ax1.plot(weights, ann_ret_list, marker='o')
    ax1.set_xlabel('纳指仓位 (%)')
    ax1.set_ylabel('年化收益率')
    ax1.set_title(f'{window_name}：纳指仓位 对比')
    ax1.set_xlim(0, 100)
    ax1.set_ylim(bottom=0)

    ax2 = ax1.twinx()
    l2, = ax2.plot(weights, ann_var_list, linestyle='--', marker='x')
    ax2.set_ylabel('年化收益方差')
    ax2.set_ylim(bottom=0)

    # 注 mark 最大 & 最小 RR
    ax1.scatter([max_w], [ann_ret_list[max_idx]], color='red', zorder=5)
    ax1.text(max_w, ann_ret_list[max_idx], f"最大RR: {max_rr:.2f}@{int(max_w)}%", color='red', ha='center', va='bottom')
    ax1.scatter([min_w], [ann_ret_list[min_idx]], color='blue', zorder=5)
    ax1.text(min_w, ann_ret_list[min_idx], f"最小RR: {min_rr:.2f}@{int(min_w)}%", color='blue', ha='center', va='top')

    # 图例放到底部
    fig.legend([l1, l2], ['年化收益率', '年化收益方差'], loc='lower center', ncol=2)
    plt.subplots_adjust(bottom=0.2)
    plt.show()

# ———— 五、构建逐年窗口并绘图 ————
years = list(range(2010, 2026))  # 2010 到 2025
windows = [(f'{y}年起', f'{y}-01-01') for y in years]

for window_name, start_date in windows:
    sub = returns.loc[returns.index >= start_date] if start_date else returns.copy()

    # 最小方差组合权重计算
    cov_mat = sub.cov().values
    inv_cov = np.linalg.inv(cov_mat)
    ones = np.ones(inv_cov.shape[0])
    w_min = inv_cov.dot(ones) / (ones.dot(inv_cov).dot(ones))
    w_ndx, w_gold = w_min

    # 最小方差组合年化指标
    ret_min = w_ndx * sub['daily_ret_ndx'] + w_gold * sub['daily_ret_gold']
    ann_ret_min = (1 + ret_min.mean())**252 - 1
    ann_var_min = ret_min.var() * 252
    ann_rr_min = ann_ret_min / ann_var_min if ann_var_min > 0 else np.nan

    print(f"{window_name} 最小方差组合权重 → 纳指 {w_ndx:.4f}, 黄金 {w_gold:.4f}")
    print(f"  年化收益率：{ann_ret_min:.2%}，年化收益方差：{ann_var_min:.6f}，单位风险收益率：{ann_rr_min:.2f}\n")

    # 绘制收益/方差对比图并标注最大与最小RR
    plot_window(sub, window_name)