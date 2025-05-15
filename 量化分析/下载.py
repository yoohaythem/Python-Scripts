# import akshare as ak
#
# # 获取沪深300历史数据
# index_df = ak.index_zh_a_hist(
#     symbol="000300",
#     period="daily",
#     start_date="20100101",
#     end_date="20250515",
# )
#
# # 保存为 Excel 文件
# index_df.to_excel("沪深300历史数据.xlsx", index=False)
#
# print("保存成功！")


import akshare as ak
import pandas as pd

# 1. 获取南方红利低波50ETF（代码：515450）的日线数据
#    返回字段中 “单位净值” 对应净值， “累计净值” 对应复权净值
df = ak.fund_open_fund_rank_em(symbol="sh512890")  # :contentReference[oaicite:0]{index=0}

# 2. 查看前几行确认数据
print(df.head())

# 3. 导出到 Excel（需要安装 openpyxl）
df.to_excel("515450_低波红利50ETF_复权净值.xlsx", index=False)
print("已保存：515450_低波红利50ETF_复权净值.xlsx")
