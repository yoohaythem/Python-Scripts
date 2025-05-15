#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np


def compute_portfolio_stats(ndx_path: str, gold_path: str):
    # 1. 读取 CSV 日线数据
    ndx = pd.read_csv(ndx_path, parse_dates=['Date'])
    gold = pd.read_csv(gold_path, parse_dates=['Date'])

    # 2. 保留收盘价并重命名
    ndx = ndx[['Date', 'Close']].rename(columns={'Close': 'NDX_Close'})
    gold = gold[['Date', 'Close']].rename(columns={'Close': 'Gold_Close'})

    # 3. 按 Date 合并
    df = pd.merge(ndx, gold, on='Date', how='inner')
    df = df.sort_values('Date').reset_index(drop=True)

    # 4. 计算每日收益率
    df['NDX_ret'] = df['NDX_Close'].pct_change()
    df['Gold_ret'] = df['Gold_Close'].pct_change()
    # 50% 黄金 + 50% 纳斯达克，初始买入后不再调仓
    df['Port_ret'] = 0.5 * df['NDX_ret'] + 0.5 * df['Gold_ret']

    # 5. 准备输出标题
    end_date = df['Date'].max()
    print(f"统计区间终止于：{end_date.date()}\n")
    header = (
        f"{'起始年':<6} {'起始日期':<6} {'累年化收益':>10} {'累年化方差':>10}{'累年化标准差':>14}"
        f"{'累简单收益':>10} {'年内收益':>9} {'年内方差':>10} {'年内标准差':>10}"
    )
    print(header)
    print('-' * int(len(header) * 1.3))

    # 6. 循环各年，计算三组指标
    for year in range(2010, end_date.year + 1):
        # —— 累计区间：每年年初第一个交易日 → 最新
        mask_start = df['Date'] >= pd.Timestamp(year, 1, 1)
        if not mask_start.any():
            continue
        start_date = df.loc[mask_start, 'Date'].min()
        period_all = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)].copy()
        period_all = period_all.dropna(subset=['Port_ret'])

        # 年化：年化收益率 & 年化方差
        days_all = len(period_all)
        years_all = days_all / 252.0
        total_ret = (period_all['Port_ret'] + 1).prod()
        ann_return = total_ret ** (1 / years_all) - 1
        ann_var = period_all['Port_ret'].var() * 252
        ann_std = np.sqrt(ann_var)
        cum_simple = total_ret - 1

        # 累计简单收益率
        cum_simple = total_ret - 1

        # —— 年内区间：自然年内（1月1日～12月31日）
        year_df = df[(df['Date'] >= pd.Timestamp(year, 1, 1)) &
                     (df['Date'] < pd.Timestamp(year + 1, 1, 1))].copy()
        year_df = year_df.dropna(subset=['Port_ret'])
        if len(year_df) > 0:
            annual_ret = (year_df['Port_ret'] + 1).prod() - 1
            annual_var = year_df['Port_ret'].var() * 252
            annual_std = np.sqrt(annual_var)
        else:
            annual_ret = np.nan
            annual_var = np.nan
            annual_std = np.nan

        # —— 打印一行
        start_str = start_date.strftime("%Y-%m-%d")
        print(
            f"{year:<6} {start_str:<12} {ann_return:12.6%} {ann_var:12.6f} {ann_std:14.6f}"
            f" {cum_simple:12.6%} {annual_ret:12.6%} {annual_var:12.6f} {annual_std:14.6f}"
        )



if __name__ == "__main__":
    # 请将下面路径替换为你的文件实际路径
    ndx_path = "^ndx_d.csv"  # 纳斯达克日线 CSV
    gold_path = "xauusd_d.csv"  # 黄金日线 CSV
    compute_portfolio_stats(ndx_path, gold_path)
