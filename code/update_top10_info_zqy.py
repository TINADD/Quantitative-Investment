import os
import tushare as ts
import pandas as pd
import datetime
import time
import numpy as np

#更新股票信息
#获取股票的[ts_code,symbol,name,area,industry,list_date]


start_date_path='181030'
end_date_path='181231'

data_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))+'/stockData/top10/'
data_path_single=data_path+ start_date_path +'_'+end_date_path+'/'

token = '92fa5b4defcb65d71defd90b46b240ad77860cc3c0ec0958e492172d'
ts.set_token(token)

pro = ts.pro_api()  #用来获取股票数据的对象
def mkdir(path):
    folder = os.path.exists(path)

    if not folder:  # 判断是否存在文件夹如果不存在则创建为文件夹
        os.makedirs(path)  # makedirs 创建文件时如果路径不存在会创建这个路径
        print("---  new folder...  ---")
        print("---  OK  ---")

    else:
        print("---  There is this folder!  ---")
mkdir(data_path)
mkdir(data_path_single)
#获取所有股票的信息（深圳交易所.SZ+上海交易所.SH） 大概有3858只股票
data = pro.stock_basic(exchange_id='', is_hs='', fields='ts_code,symbol,name,area,industry,list_date')
#print(data['ts_code'])
#print('将所有股票的信息保存到一个文件中')
#data.to_csv(data_path+'stock_info_1007.csv',index=False)

#更新十大股东占比
#[ts_code,hold_ratio,top10_d_r] top10_d_r =hold_ratio
top10_holders_saved_path = "" #数据保存在当前目录下
top10_holders = pd.DataFrame()
for code in data['ts_code']:
    print(code)
    try:
    #获取股票code的十大股东
        time.sleep(0.1)
        df = pro.top10_holders(ts_code=code,start_date='20171030',end_date='20181231')#获取数据
    except:
     #如果获取数据超时，停0.2秒重新获取
        time.sleep(2)
        df = pro.top10_holders(ts_code=code,start_date='20171030',end_date='20181231')
    if df.empty:
        continue
    df.to_csv(data_path_single+str(code)+'.csv',index=False,encoding='utf-8')
    #df=pd.read_csv(data_path+str(code)+'.csv')
    #选取最新的几个股东求和hold_ratio
    #df = df[df['ann_date'] == df.iloc[0,1]]#取0行1列，只选取了日期是最新日期的数据
    #df = df[df['end_date'] == df.iloc[0,2]]
    df = df.drop_duplicates(subset = None,keep = 'first')#去除完全重复的数据
    #df = df.drop_duplicates(['holder_name'])#去重
    #print(df)
    dateInfo = df['end_date'].unique()
    #print(dateInfo)
    DATE = {}
    for temp_date in dateInfo:
        DATE=df[df['end_date'].isin([temp_date])]
        DATE=DATE.drop_duplicates(subset = None,keep = 'first')#去重
        DATE = DATE[['ts_code', 'end_date', 'hold_ratio']]
        #print(DATE)
        if len(DATE)<10: continue
        DATE['hold_ratio']=DATE['hold_ratio'].sum()#会生成10行一样的数据
        DATE=DATE.drop_duplicates(['end_date'])
        top10_holders = pd.concat([top10_holders,DATE])#合并
#TODO[0]:将不同日期的占比和根据日期分开存
top10_holders['top10_d_r'] = top10_holders['hold_ratio']
print(top10_holders)
print("将top10保存到文件")
top10_holders.to_csv(data_path+'top10_2018_scoure.csv',index=False)
top10_holders=top10_holders.drop_duplicates(['ts_code'])
top10_holders.to_csv(data_path+'top10_2018.csv',index=False)