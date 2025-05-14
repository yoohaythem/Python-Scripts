import time

import pandas as pd
import tushare as ts
import numpy as np
import math
from pandas_datareader import data as web


# 单只股票在不同年份中的夏普比率
def single_stock():
    ts.set_token('995776e5cebde1974a4fbab03deb2a5a7b91badb4e03070172a28f6e')
    pro = ts.pro_api()
    print(pro.user(token='995776e5cebde1974a4fbab03deb2a5a7b91badb4e03070172a28f6e'))

    # df1 = pro.fund_basic(market='O', ts_code='160222.OF')
    df2 = pro.daily(ts_code='160222.OF', start_date='20200601', end_date='20200813')
    df3 = pro.daily(ts_code='150018.SZ', start_date='20180101', end_date='20181029')
    print(df2)

    # 贵州茅台
    df4_1 = pro.daily(ts_code='600519.SH', start_date='20200101', end_date='20201231')
    df4_2 = pro.daily(ts_code='600519.SH', start_date='20190101', end_date='20191231')
    df4_3 = pro.daily(ts_code='600519.SH', start_date='20180101', end_date='20181231')
    df4_4 = pro.daily(ts_code='600519.SH', start_date='20170101', end_date='20171231')
    df4_5 = pro.daily(ts_code='600519.SH', start_date='20160101', end_date='20161231')
    df4_6 = pro.daily(ts_code='600519.SH', start_date='20150101', end_date='20151231')
    years = [df4_1, df4_2, df4_3, df4_4, df4_5, df4_6]

    for x in range(2024, 2010, -1):
        df = pro.index_daily(ts_code='399300.SZ', start_date=str(x) + '0101', end_date=str(x) + '1231')
        a = np.log(df['close'].shift(1) / df['close'])
        sharpe = (a.mean() * 252 - 0.014) / (a.std() * math.sqrt(252))
        print('sharpe in ' + str(x) + ' = ' + str('%.4f' % sharpe))


single_stock()


# A股主要股指、股票过去十年的夏普指数
def Chinese_index():
    ts.set_token('995776e5cebde1974a4fbab03deb2a5a7b91badb4e03070172a28f6e')
    pro = ts.pro_api()
    lists_1 = ['000001.SH', '399001.SZ', '399300.SZ', '399006.SZ']
    lists_2 = ['600519.SH', '002230.SZ']
    lists = lists_1 + lists_2
    table = pd.DataFrame([], columns=['2020', '2019', '2018', '2017', '2016', '2015', '2014', '2013', '2012', '2011'],
                         index=lists)

    for one in lists_1:
        for x in range(2020, 2010, -1):
            df = pro.index_daily(ts_code=one, start_date=str(x) + '0101', end_date=str(x) + '1231')
            a = np.log(df['close'].shift(1) / df['close'])
            sharpe = (a.mean() * 252 - 0.014) / (a.std() * math.sqrt(252))
            # print(str(one) + ' sharpe in '+str(x)+' = '+str('%.4f' % sharpe))
            table[str(x)][one] = '%.4f' % sharpe

    for one in lists_2:
        for x in range(2020, 2010, -1):
            df = pro.daily(ts_code=one, start_date=str(x) + '0101', end_date=str(x) + '1231')
            a = np.log(df['close'].shift(1) / df['close'])
            sharpe = (a.mean() * 252 - 0.014) / (a.std() * math.sqrt(252))
            # print(str(one) + ' sharpe in '+str(x)+' = '+str('%.4f' % sharpe))
            table[str(x)][one] = '%.4f' % sharpe
    print(table)
    table.to_excel('C://quant//Chinese stock index.xlsx')


# 美股主要股指、股票过去十年的夏普指数
def American_index():
    lists_1 = ['^IXIC', 'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'TSLA', '^HSI', '0700.hk']
    lists_2 = ['BABA']
    lists_3 = ['FB']
    lists = lists_1 + lists_2 + lists_3
    lists = ['^IXIC']
    table = pd.DataFrame([], columns=['2020', '2019', '2018', '2017', '2016', '2015', '2014', '2013', '2012', '2011'],
                         index=lists)

    for one in lists:
        for x in range(2020, 2010, -1):
            df = web.DataReader(name=one, data_source='yahoo', start=str(x) + '0101', end=str(x) + '1231')
            a = np.log(df['Close'] / df['Close'].shift(1))
            sharpe = (a.mean() * 252 - 0.014) / (a.std() * math.sqrt(252))
            table[str(x)][one] = '%.4f' % sharpe

    for one in lists_2:
        for x in range(2020, 2014, -1):
            df = web.DataReader(name=one, data_source='yahoo', start=str(x) + '0101', end=str(x) + '1231')
            a = np.log(df['Close'] / df['Close'].shift(1))
            sharpe = (a.mean() * 252 - 0.014) / (a.std() * math.sqrt(252))
            table[str(x)][one] = '%.4f' % sharpe

    for one in lists_3:
        for x in range(2020, 2012, -1):
            df = web.DataReader(name=one, data_source='yahoo', start=str(x) + '0101', end=str(x) + '1231')
            a = np.log(df['Close'] / df['Close'].shift(1))
            sharpe = (a.mean() * 252 - 0.014) / (a.std() * math.sqrt(252))
            table[str(x)][one] = '%.4f' % sharpe

    print(table)
    # table.to_excel('C://quant//American stock market.xlsx')


# A股一级行业指数过去十年的夏普指数
def Primary_industry():
    ts.set_token('995776e5cebde1974a4fbab03deb2a5a7b91badb4e03070172a28f6e')
    pro = ts.pro_api()
    df_x = pro.index_basic(market='SW', category='一级行业指数')
    table = pd.DataFrame([], columns=['name', '2020', '2019', '2018', '2017', '2016', '2015', '2014', '2013', '2012', '2011'])
    table['name'] = df_x['name']
    table.index = df_x['ts_code']

    for one in df_x['ts_code']:
        for x in range(2020, 2015, -1):
            df = pro.index_weekly(ts_code=str(one), start_date=str(x) + '0101', end_date=str(x) + '1231')
            a = np.log(df['close'].shift(1) / df['close'])
            sharpe = (a.mean() * 52 - 0.014) / (a.std() * math.sqrt(52))
            # print(str(one) + ' sharpe in '+str(x)+' = '+str('%.4f' % sharpe))
            table[str(x)][one] = '%.4f' % sharpe
    print(table)
    table.to_csv('C://quant//Primary industry‘s sharpe.xlsx')


# A股二级行业指数过去十年的夏普指数
def Secondary_industry():
    ts.set_token('995776e5cebde1974a4fbab03deb2a5a7b91badb4e03070172a28f6e')
    pro = ts.pro_api()
    df_x = pro.index_basic(market='SZSE', category='综合指数')
    table = pd.DataFrame([], columns=['name', '2020', '2019', '2018', '2017', '2016', '2015', '2014', '2013', '2012', '2011'])
    table['name'] = df_x['name']
    table.index = df_x['ts_code']

    for one in df_x['ts_code']:
        for x in range(2020, 2019, -1):
            df = pro.index_daily(ts_code=str(one), start_date=str(x) + '0101', end_date=str(x) + '1231')
            a = np.log(df['close'].shift(1) / df['close'])
            sharpe = (a.mean() * 252 - 0.014) / (a.std() * math.sqrt(252))
            # print(str(one) + ' sharpe in '+str(x)+' = '+str('%.4f' % sharpe))
            table[str(x)][one] = '%.4f' % sharpe
    print(table)
    table.to_excel('C://quant//Secondary industry‘s sharpe.xlsx')
