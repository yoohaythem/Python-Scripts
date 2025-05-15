#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np

def compute_hs300_stats(excel_path: str):
    # 1. 读取并排序
    df = pd.read_excel(excel_path, parse_dates=['日期'])
    df = df.sort_values('日期').reset_index(drop=True)

    # 2. 确定最新日期与收盘价
    end_date = df['日期'].max()
    end_price = df.loc[df['日期'] == end_date, '收盘'].iat[0]

    # 3. 打印表头
    print(f"统计区间终止于：{end_date.date()}\n")
    header = (
        f"{'起始年':<6} {'起始日期':<6} {'累年化收益':>10} {'累年化方差':>10}{'累年化标准差':>14}"
        f"{'累简单收益':>10} {'年内收益':>9} {'年内方差':>10} {'年内标准差':>10}"
    )
    print(header)
    print('-' * int(len(header) * 1.3))

    # 4. 循环各年计算指标
    for year in range(2010, end_date.year + 1):
        # 累计区间：当年年初第一个交易日 → 最新
        mask_start = df['日期'] >= pd.Timestamp(year, 1, 1)
        if not mask_start.any():
            continue
        start_date = df.loc[mask_start, '日期'].min()
        start_price = df.loc[df['日期'] == start_date, '收盘'].iat[0]

        period_all = df[(df['日期'] >= start_date) & (df['日期'] <= end_date)]
        daily_ret_all = period_all['收盘'].pct_change().dropna()

        days_all  = len(daily_ret_all)
        years_all = days_all / 252.0
        total_ret = end_price / start_price
        ann_return = total_ret ** (1 / years_all) - 1
        ann_var    = daily_ret_all.var() * 252
        ann_std = np.sqrt(ann_var)
        cum_simple = total_ret - 1

        # 年内区间：自然年内（1月1日～12月31日）
        period_year = df[
            (df['日期'] >= pd.Timestamp(year, 1, 1)) &
            (df['日期'] <  pd.Timestamp(year + 1, 1, 1))
        ]
        daily_ret_year = period_year['收盘'].pct_change().dropna()
        if len(daily_ret_year) > 0:
            annual_return = (period_year['收盘'].iloc[-1] / period_year['收盘'].iloc[0]) - 1
            annual_var    = daily_ret_year.var() * 252
            annual_std = np.sqrt(annual_var)
        else:
            annual_return = np.nan
            annual_var = np.nan
            annual_std = np.nan

        # 输出对齐
        start_str = start_date.strftime("%Y-%m-%d")
        print(
            f"{year:<6} {start_str:<12} {ann_return:12.6%} {ann_var:12.6f} {ann_std:14.6f}"
            f" {cum_simple:12.6%} {annual_return:12.6%} {annual_var:12.6f} {annual_std:14.6f}"
        )

if __name__ == "__main__":
    excel_path = "沪深300历史数据.xlsx"  # 替换为你的文件路径
    compute_hs300_stats(excel_path)
