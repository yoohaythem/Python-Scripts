#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np

def backtest_ndx(csv_path: str):
    # 1. 读取并排序
    df = pd.read_csv(csv_path, parse_dates=['Date'])
    df = df.sort_values('Date').reset_index(drop=True)

    # 2. 确定最新日期与收盘价
    end_date  = df['Date'].max()
    end_price = df.loc[df['Date'] == end_date, 'Close'].iat[0]

    # 3. 打印表头
    header = (
        f"{'起始年':<6} {'起始日期':<6} {'累年化收益':>10} {'累年化方差':>10}{'累年化标准差':>14}"
        f"{'累简单收益':>10} {'年内收益':>9} {'年内方差':>10} {'年内标准差':>10}"
    )
    print(header)
    print('-' * int(len(header) * 1.3))

    # 4. 循环各年
    for year in range(2010, end_date.year + 1):
        # 从年初第一个交易日
        mask = df['Date'] >= pd.Timestamp(year, 1, 1)
        if not mask.any():
            continue
        start_date = df.loc[mask, 'Date'].min()
        start_price = df.loc[df['Date'] == start_date, 'Close'].iat[0]

        period_all = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
        ret_daily_all = period_all['Close'].pct_change().dropna()
        days_all = len(ret_daily_all)
        years_all = days_all / 252.0

        total_ret = end_price / start_price
        ann_return = total_ret ** (1/years_all) - 1
        ann_var    = ret_daily_all.var() * 252
        ann_std = np.sqrt(ann_var)
        cum_simple = total_ret - 1

        # 年内
        period_year = df[
            (df['Date'] >= pd.Timestamp(year, 1, 1)) &
            (df['Date'] <  pd.Timestamp(year+1, 1, 1))
        ]
        ret_daily_y = period_year['Close'].pct_change().dropna()
        if len(ret_daily_y):
            annual_ret   = (period_year['Close'].iloc[-1] / period_year['Close'].iloc[0]) - 1
            annual_var   = ret_daily_y.var() * 252
            annual_std = np.sqrt(annual_var)
        else:
            annual_ret = np.nan
            annual_var = np.nan
            annual_std = np.nan

        start_str = start_date.strftime("%Y-%m-%d")
        print(
            f"{year:<6} {start_str:<12} {ann_return:12.6%} {ann_var:12.6f} {ann_std:14.6f}"
            f" {cum_simple:12.6%} {annual_ret:12.6%} {annual_var:12.6f} {annual_std:14.6f}"
        )

if __name__ == "__main__":
    # 修改为你的纳斯达克数据 CSV 路径
    ndx_csv = "^ndx_d.csv"
    backtest_ndx(ndx_csv)
