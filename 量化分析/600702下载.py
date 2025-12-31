import akshare as ak

# 获取舍得酒业历史数据
stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol="600702", period="daily",
                                        start_date="20100101",
                                        end_date="20250831")  # qfq表示前复权
print(stock_zh_a_hist_df.head())
stock_zh_a_hist_df.to_csv("shede_jiuye_historical_data.csv")