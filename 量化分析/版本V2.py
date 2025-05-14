import pandas as pd
import numpy as np
from IPython.display import display  # Jupyter 环境下使用

# 显示所有行、所有列
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

# 1. 读取并排序
纳指 = pd.read_csv('^ndx_d.csv', parse_dates=['Date']).sort_values('Date')
黄金 = pd.read_csv('xauusd_d.csv', parse_dates=['Date']).sort_values('Date')

# 2. 归一化收盘（各以1元初始资金）
纳指['归一化收盘'] = 纳指['Close'] / 纳指['Close'].iloc[0]
黄金['归一化收盘'] = 黄金['Close'] / 黄金['Close'].iloc[0]

# 3. 计算日收益率
纳指['日收益'] = 纳指['归一化收盘'].pct_change()
黄金['日收益'] = 黄金['归一化收盘'].pct_change()

# 4. 合并日收益并去 NaN，设置索引
收益_df = (
    pd.merge(
        纳指[['Date', '日收益']],
        黄金[['Date', '日收益']],
        on='Date',
        suffixes=['_ndx', '_gold']
    )
        .dropna()
        .set_index('Date')
)

# 5. 定义时间窗口
窗口列表 = [
    ('全部', None),
    ('2015‑起', '2015-01-01'),
    ('2020‑起', '2020-01-01'),
]

年化因子 = 252
最终结果 = []

# 6. 针对每个窗口，计算最小方差组合及固定仓位组合
for 窗口名, 起始日 in 窗口列表:
    # 取子集
    if 起始日:
        df_sub = 收益_df.loc[收益_df.index >= 起始日]
    else:
        df_sub = 收益_df.copy()

    # 6.1 计算最小方差权重
    cov_mat = df_sub.cov().values
    inv_cov = np.linalg.inv(cov_mat)
    ones = np.ones(inv_cov.shape[0])
    raw_w = inv_cov.dot(ones)
    w_min = raw_w / (ones.dot(inv_cov).dot(ones))
    w_min_ndx, w_min_gold = w_min

    # 计算最小方差组合的年化收益 & 年化方差
    ret_min = w_min_ndx * df_sub['日收益_ndx'] + w_min_gold * df_sub['日收益_gold']
    mean_ret = ret_min.mean()
    ann_ret = (1 + mean_ret) ** 年化因子 - 1
    var_min = ret_min.var() * 年化因子

    最小行 = {
        '窗口': 窗口名,
        '组合': '最小方差组合',
        '纳指权重': f"{w_min_ndx:.4f}",
        '黄金权重': f"{w_min_gold:.4f}",
        '年化收益率': f"{ann_ret:.2%}",
        '年化收益方差': f"{var_min:.6f}"
    }
    最终结果.append(最小行)

    # 6.2 固定仓位 5%-100%
    for p in np.arange(0.05, 1.001, 0.05):
        w_ndx = p
        w_gold = 1 - p
        ret_p = w_ndx * df_sub['日收益_ndx'] + w_gold * df_sub['日收益_gold']
        mean_p = ret_p.mean()
        ann_p = (1 + mean_p) ** 年化因子 - 1
        var_p = ret_p.var() * 年化因子

        最终结果.append({
            '窗口': 窗口名,
            '组合': f"NDX {int(p * 100)}% / Gold {int((1 - p) * 100)}%",
            '纳指权重': f"{w_ndx:.2f}",
            '黄金权重': f"{w_gold:.2f}",
            '年化收益率': f"{ann_p:.2%}",
            '年化收益方差': f"{var_p:.6f}"
        })

# 7. 汇总展示
结果表 = pd.DataFrame(最终结果)
display(结果表)
