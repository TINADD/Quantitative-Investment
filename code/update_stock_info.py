import os
import tushare as ts
import pandas as pd
import datetime
import time
import numpy as np

#更新股票信息
#获取股票的[ts_code,symbol,name,area,industry,list_date]

stock_saved_path = './' #股票信息文件保存在当前目录下
top10_saved_path="../stockData/top10/"
token = '92fa5b4defcb65d71defd90b46b240ad77860cc3c0ec0958e492172d'
ts.set_token(token)

pro = ts.pro_api()  #用来获取股票数据的对象

#获取所有股票的信息（深圳交易所.SZ+上海交易所.SH） 大概有3858只股票
data = pro.stock_basic(exchange_id='', is_hs='', fields='ts_code,symbol,name,area,industry,list_date')
#print(data['ts_code'])
#print('将所有股票的信息保存到一个文件中')
#data.to_csv(stock_saved_path+'stock_info_1007.csv',index=False)

#更新十大股东占比
#[ts_code,hold_ratio,top10_d_r] top10_d_r =hold_ratio
top10_holders_saved_path = "" #数据保存在当前目录下
top10_holders = pd.DataFrame()
print('top10')
for code in data['ts_code']:
    print(code)
    try:
        #获取股票code的十大股东
        time.sleep(0.1)
        df = pro.top10_holders(ts_code=code,start_date='20200101',end_date='20201125')
    except:
        #如果获取数据超时，停0.2秒重新获取
        time.sleep(2)
        df = pro.top10_holders(ts_code=code,start_date='20200101',end_date='20201125')
    if df.empty:
        continue
    #df.to_csv(top10_saved_path+str(code)+'.csv',index=False,encoding='utf-8')
    df=pd.read_csv(top10_saved_path+str(code)+'.csv')
    #选取最新的几个股东求和hold_ratio
    df = df[df['ann_date'] == df.iloc[0,1]]#日期只选了最新的
    df = df[df['end_date'] == df.iloc[0,2]]
    df = df.drop_duplicates(['holder_name'])
    df['hold_ratio'] = df['hold_ratio'].sum()
    df = df.drop_duplicates(['hold_ratio'])
    df = df[['ts_code','hold_ratio']]
    #print(df)
    top10_holders = pd.concat([top10_holders,df])
    #print(top10_holders)
    #top10_holders.to_csv(stock_saved_path+'top10_1007.csv',index=False)

top10_holders['top10_d_r'] = top10_holders['hold_ratio']
print(top10_holders)
print("将top10保存到文件")
top10_holders.to_csv(stock_saved_path+'top10_1125.csv',index=False)