import os
import tushare as ts
import pandas as pd
import datetime
import time
import numpy as np
import sys

#stock_daily_path = 'F:/SmartLab/stockData/20200101_20201101/daily_stocks.csv'
cur_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
#stock_daily = pd.read_csv(stock_daily_path)
token = '92fa5b4defcb65d71defd90b46b240ad77860cc3c0ec0958e492172d'
ts.set_token(token)

pro = ts.pro_api()  #用来获取股票数据的对象
data = pro.stock_basic(exchange_id='', is_hs='', fields='ts_code,symbol,name,area,industry,list_date')
top10_df = pd.DataFrame()

#获取给定时间段的十大股东数据
end_time = '20200301'
beg_time = '20190301'
for code in data['ts_code'] :
    #print(code,'\n')
    #print(beg_time,end_time,'\n')
    try:
        #获取股票code的十大股东
        time.sleep(0.1)
        df = pro.top10_holders(ts_code=code,start_date=beg_time,end_date=end_time)
    except:
        #如果获取数据超时，停0.2秒重新获取
        time.sleep(2)
        df = pro.top10_holders(ts_code=code,start_date=beg_time,end_date=end_time)
    if df.empty:
        print(df)
        continue
    #选取最新的几个股东求和hold_ratio
    df = df[df['ann_date'] == df.iloc[0,1]]
    df = df[df['end_date'] == df.iloc[0,2]]
    df = df.drop_duplicates(['holder_name'])
    df['hold_ratio'] = df['hold_ratio'].sum()
    df = df.drop_duplicates(['hold_ratio'])
    #print(df['hold_ratio'])
    #test = stock_daily[(stock_daily['code'] == ccode) & (stock_daily['datetime'] == day)]
    #test.iloc[0,14] = 10
    df = df[['ts_code','hold_ratio']]
    #print(stock_daily[(stock_daily['code'] == ccode) & (stock_daily['datetime'] == day)])
    #print(test.iloc[0,14])
    top10_df = pd.concat([top10_df,df])
    #print(top10_holders)
top10_df['top10_d_r'] = top10_df['hold_ratio']
top10_df.to_csv(cur_dir+'/top10_1125.csv',index=False)   
        
