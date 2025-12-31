import pandas as pd
import numpy as np
import matplotlib

# 设置matplotlib后端，避免警告
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 尝试不同编码方式读取CSV文件
encodings = ['gbk', 'gb2312', 'utf-8', 'latin1']

df = None
for encoding in encodings:
    try:
        print(f"尝试使用 {encoding} 编码读取文件...")
        df = pd.read_csv('shede_jiuye_historical_data.csv', encoding=encoding)
        print(f"成功使用 {encoding} 编码读取文件")
        break
    except UnicodeDecodeError:
        print(f"{encoding} 编码失败")
        continue
    except FileNotFoundError:
        print("文件未找到，请确保文件路径正确")
        break

if df is None:
    print("无法读取文件，请检查文件编码或路径")
    exit()

# 显示数据前几行和列名，以便确认数据结构
# print("数据前5行:")
# print(df.head())
# print("\n数据列名:")
# print(df.columns.tolist())

# 重命名列名为标准名称
column_mapping = {
    '日期': ['日期', 'date', 'Date', '交易日期'],
    '开盘': ['开盘', 'open', 'Open', '开盘价'],
    '收盘': ['收盘', 'close', 'Close', '收盘价'],
    '最高': ['最高', 'high', 'High', '最高价'],
    '最低': ['最低', 'low', 'Low', '最低价']
}

# 标准化列名
standard_columns = {}
for standard_name, possible_names in column_mapping.items():
    for name in possible_names:
        if name in df.columns:
            standard_columns[name] = standard_name
            break

if not standard_columns:
    print("无法识别列名，请手动指定列名映射")
    exit()

df.rename(columns=standard_columns, inplace=True)

# 确保日期列是日期时间格式
df['日期'] = pd.to_datetime(df['日期'])

# 筛选2024年后的数据
df = df[df['日期'] >= '2019-01-01'].reset_index(drop=True)

if df.empty:
    print("2024年后的数据为空，请检查数据日期范围")
    exit()

# 计算每日涨跌幅
df['涨跌幅'] = df['收盘'].pct_change() * 100

# 初始化变量
initial_stock_value = 500000  # 初始股票市值25万
initial_cash = 500000  # 初始现金75万
initial_capital = initial_stock_value + initial_cash  # 总初始资金100万

# 使用金额而不是股数来表示持有股票
stock_value = initial_stock_value  # 初始股票市值
cash = initial_cash  # 初始现金

trade_target = 50000  # 目标交易金额5万
max_stock_value = 1000000  # 最大股票市值100万
min_stock_value = 0  # 最小股票市值0

# 手续费参数
commission_rate = 0.0001  # 佣金率0.03%
min_commission = 5  # 最低佣金5元
stamp_duty_rate = 0.001  # 印花税率0.1%（仅卖出时收取）
transfer_fee_rate = 0.00002  # 过户费率0.002%

# 记录每日资产和交易明细
daily_assets = []
trade_log = []

# 回测循环
for i, row in df.iterrows():
    date = row['日期']
    close_price = row['收盘']
    pct_change = row['涨跌幅']

    # 计算总资产
    total_assets = cash + stock_value
    daily_assets.append({
        '日期': date,
        '总资产': total_assets,
        '现金': cash,
        '股票市值': stock_value,
        '股价': close_price
    })

    # 如果是第一天，跳过交易判断
    if i == 0 or pd.isna(pct_change):
        # 每天股票市值会根据股价变化（除了第一天）
        continue

    # 每天股票市值会根据股价变化
    # 这里我们模拟股票市值的变化（基于前一天的市值和当天的涨跌幅）
    stock_value = stock_value * (1 + pct_change / 100)

    # 交易逻辑
    transaction_type = None
    transaction_value = 0
    commission = 0
    stamp_duty = 0
    transfer_fee = 0

    if pct_change >= 7 and stock_value > 0:  # 涨幅≥1%，卖出约5万
        # 计算卖出金额（尽量接近5万，但不超出当前股票市值）
        sell_value = min(trade_target, stock_value)

        # 计算手续费
        commission = max(sell_value * commission_rate, min_commission)
        stamp_duty = sell_value * stamp_duty_rate  # 印花税（卖出时收取）
        transfer_fee = sell_value * transfer_fee_rate  # 过户费

        # 总手续费
        total_fees = commission + stamp_duty + transfer_fee

        # 实际收到的金额
        net_proceeds = sell_value - total_fees

        # 更新现金和股票市值
        cash += net_proceeds
        stock_value -= sell_value

        transaction_type = "卖出"
        transaction_value = sell_value

    elif pct_change <= -7 and cash > 0:  # 跌幅≤-1%，买入约5万
        # 计算买入金额（尽量接近5万，但不超出当前现金和最大股票市值限制）
        buy_value = min(trade_target, cash, max_stock_value - stock_value)

        if buy_value > 0:
            # 计算手续费
            commission = max(buy_value * commission_rate, min_commission)
            transfer_fee = buy_value * transfer_fee_rate  # 过户费

            # 总手续费
            total_fees = commission + transfer_fee

            # 实际用于购买股票的资金
            net_investment = buy_value - total_fees

            # 更新现金和股票市值
            cash -= buy_value
            stock_value += net_investment

            transaction_type = "买入"
            transaction_value = buy_value

    # 记录交易明细（如果有交易）
    if transaction_type:
        trade_log.append({
            '日期': date,
            '类型': transaction_type,
            '金额': transaction_value,
            '佣金': commission,
            '印花税': stamp_duty,
            '过户费': transfer_fee,
            '股价': close_price
        })

# 创建结果DataFrame
results_df = pd.DataFrame(daily_assets)

# 计算最终收益
final_assets = results_df.iloc[-1]['总资产']
profit = final_assets - initial_capital
profit_rate = (profit / initial_capital) * 100

# 计算总手续费
total_commission = sum(trade['佣金'] for trade in trade_log)
total_stamp_duty = sum(trade['印花税'] for trade in trade_log)
total_transfer_fee = sum(trade['过户费'] for trade in trade_log)
total_fees = total_commission + total_stamp_duty + total_transfer_fee

print("=" * 50)
print("舍得酒业回测结果（含手续费）")
print("=" * 50)
print(f"回测期间: {df['日期'].min().strftime('%Y-%m-%d')} 至 {df['日期'].max().strftime('%Y-%m-%d')}")
print(f"初始总资产: {initial_capital:,.2f}元 (股票: {initial_stock_value:,.2f}元, 现金: {initial_cash:,.2f}元)")
print(f"最终总资产: {final_assets:,.2f}元")
print(f"盈利: {profit:,.2f}元")
print(f"收益率: {profit_rate:.2f}%")
print(f"交易次数: {len(trade_log)}次")
print(f"总手续费: {total_fees:,.2f}元")
print(f"  佣金: {total_commission:,.2f}元")
print(f"  印花税: {total_stamp_duty:,.2f}元")
print(f"  过户费: {total_transfer_fee:,.2f}元")
print("=" * 50)

# 绘制资产趋势图
plt.figure(figsize=(14, 10))

# 资产趋势
plt.subplot(2, 2, 1)
plt.plot(results_df['日期'], results_df['总资产'], label='总资产', linewidth=2, color='blue')
plt.plot(results_df['日期'], results_df['股票市值'], label='股票市值', linestyle='--', color='green')
plt.plot(results_df['日期'], results_df['现金'], label='现金', linestyle=':', color='red')
plt.title('舍得酒业回测 - 资产趋势')
plt.ylabel('金额 (元)')
plt.legend()
plt.grid(True)
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
plt.gcf().autofmt_xdate()

# 股价趋势
plt.subplot(2, 2, 2)
plt.plot(results_df['日期'], results_df['股价'], label='股价', color='purple', linewidth=2)
plt.title('舍得酒业股价走势')
plt.ylabel('股价 (元)')
plt.grid(True)
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
plt.gcf().autofmt_xdate()

# 资产构成比例
plt.subplot(2, 2, 3)
stock_ratio = results_df['股票市值'] / results_df['总资产'] * 100
cash_ratio = results_df['现金'] / results_df['总资产'] * 100
plt.plot(results_df['日期'], stock_ratio, label='股票占比', color='orange', linewidth=2)
plt.plot(results_df['日期'], cash_ratio, label='现金占比', color='brown', linewidth=2)
plt.title('资产构成比例')
plt.ylabel('占比 (%)')
plt.legend()
plt.grid(True)
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
plt.gcf().autofmt_xdate()

# 收益率曲线
plt.subplot(2, 2, 4)
returns = (results_df['总资产'] - initial_capital) / initial_capital * 100
plt.plot(results_df['日期'], returns, label='收益率', color='brown', linewidth=2)
plt.title('收益率曲线')
plt.ylabel('收益率 (%)')
plt.grid(True)
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
plt.gcf().autofmt_xdate()

plt.tight_layout()
plt.savefig('舍得酒业回测结果.png', dpi=300)
plt.show()

# 输出每日资产明细到CSV
results_df.to_csv('舍得酒业每日资产明细.csv', index=False, encoding='utf-8-sig')

# 输出交易明细到CSV
if trade_log:
    trade_df = pd.DataFrame(trade_log)
    trade_df.to_csv('舍得酒业交易明细.csv', index=False, encoding='utf-8-sig')

    # 打印最近5笔交易
    print("\n最近5笔交易明细:")
    print(trade_df.tail().to_string(index=False))
else:
    print("回测期间没有发生交易")

# 输出统计信息
print("\n回测统计信息:")
print(f"最大资产: {results_df['总资产'].max():,.2f}元")
print(f"最小资产: {results_df['总资产'].min():,.2f}元")
print(f"最终现金: {results_df.iloc[-1]['现金']:,.2f}元")
print(f"最终股票市值: {results_df.iloc[-1]['股票市值']:,.2f}元")
print(f"最高股票占比: {stock_ratio.max():.2f}%")
print(f"最低股票占比: {stock_ratio.min():.2f}%")