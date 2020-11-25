# -*- coding: utf-8 -*-
"""
Created on Sat Nov 16 15:29:18 2019

@author: PC

获取新属性 - 前22个交易日最高与最低之差

@author: PC
"""

import os
import tushare as ts
import pandas as pd
import datetime
import time
import numpy as np
import sys

def mkdir(path):
 
	folder = os.path.exists(path)
 
	if not folder:                   #判断是否存在文件夹如果不存在则创建为文件夹
		os.makedirs(path)            #makedirs 创建文件时如果路径不存在会创建这个路径
		print ("---  new folder...  ---")
		print ("---  OK  ---")
 
	else:
		print ("---  There is this folder!  ---")


token = '92fa5b4defcb65d71defd90b46b240ad77860cc3c0ec0958e492172d'
ts.set_token(token)

cur_dir_path = os.path.dirname(os.path.realpath(sys.argv[0]))
print(cur_dir_path)

#给定下载日期，比如要测试19年11月到现在的数据，需要从19年10月开始下载
#获取20191101-20200620之间的股票数据
#获取20200101-20200630之间的股票数据
#获取20200101-20201001之间的股票数据[0101,1001)
#获取20200101-20201101之间的股票数据[0101,1001)
start_date_bef = '20191201' #从当前日期开始下载
start_date_rel = '20200101' #实际需要的起始日期
end_date = '20201101' #实际的要获取股票数据的结束日期,获取结果不含该日期

saved_path = 'F:/Smart实验室/量化投资/dataDownload/'+start_date_rel+'_'+end_date+'/' #当前程序下载的所有文件都存在此目录下
daily_path = saved_path+'DailySingle/' #日线数据存储路径，一只股票一个文件
fq_path = saved_path+'fqSingle/'  #复权因子存储路径，一只股票一个文件
final_save_path = saved_path   #存储总的日线数据和复权因子数据


mkdir(saved_path)
mkdir(daily_path)
mkdir(fq_path)
mkdir(final_save_path)


#Final whole file path and name
final_daily_path = saved_path +'allStocksDaily-'+start_date_rel + '_'+ end_date + '.csv'  #所有股票的日线数据,放到此文件里

single_path = daily_path   #单只股票的日线数据存储路径
#未经处理过的日线数据-单只股票的日线数据存储路径
single_path_source = saved_path + 'DailySingleSource/'
mkdir(single_path)
mkdir(single_path_source)

pro = ts.pro_api()  #用来获取股票数据的对象
#获取所有股票的信息（深圳交易所.SZ+上海交易所.SH） 大概有3858只股票
data = pro.stock_basic(exchange_id='', is_hs='', fields='ts_code,symbol,name,list_date,list_status')
#Save the stock id if it has got the daily and fq data.
Get_info_list = []
#Save the final stock daily info.
#final_df = pd.DataFrame() 
daily_stocks = pd.DataFrame() #所有股票的日线数据 
#final_source_df = pd.DataFrame()
daily_stocks_source = pd.DataFrame() #所有股票未处理的日线数据
#fq_final_df = pd.DataFrame()  
fq_stocks = pd.DataFrame()#所有股票的复权因子

#cq stocks
cq_stocks_list = []
#Error stock list 
error_list = []

daily_stocks = pd.read_csv(daily_path + 'tmpDaily.csv')
daily_stocks_source = pd.read_csv(single_path_source + 'tmpDailySource.csv')
'''注意已经有原始价格了，不需要再下载一次了，直接对final_source_df和final_df进行操作。需补上这段代码。'''
#总市值信息
daily_stocks_source = daily_stocks_source[['trade_date','ts_code','total_share','pre_close']]
#final_source_df = final_source_df[['trade_date','ts_code','total_share','pre_close']]
print("daily_stocks_source['total_share'] : \n")
print(daily_stocks_source['total_share'])
print("daily_stocks_source['pre_close'] : \n")
print(daily_stocks_source['pre_close'])
daily_stocks_source['totals1'] = daily_stocks_source['total_share']*daily_stocks_source['pre_close']
print("daily_stocks_source['totals1'] \n")
print(daily_stocks_source[daily_stocks_source['ts_code'] == '300330.SZ']['totals1'])
#final_source_df['totals1'] = final_source_df['total_share']*final_source_df['pre_close']
print("daily_stocks_source['trade_date'] \n")
print(daily_stocks_source[daily_stocks_source['ts_code'] == '300330.SZ'][['trade_date','ts_code','totals1']])
daily_stocks_source['trade_date'] = pd.to_datetime(daily_stocks_source['trade_date'],errors='raise',format='%Y-%m-%d')

daily_stocks['trade_date'] = pd.to_datetime(daily_stocks['trade_date'])

print("daily_stocks_source['trade_date'] \n")
print(daily_stocks_source[daily_stocks_source['ts_code'] == '300330.SZ'][['trade_date','ts_code','totals1']])

print("daily_stocks['trade_date'] \n")
print(daily_stocks[daily_stocks['ts_code'] == '300330.SZ'][['trade_date','ts_code']])
#final_source_df['trade_date'] = pd.to_datetime(final_source_df['trade_date'])
daily_stocks_tmp = pd.merge(daily_stocks,daily_stocks_source,on=['trade_date','ts_code'],how='left')
print("1 daily_stocks_tmp['totals1'] \n")
print(daily_stocks_tmp[daily_stocks_tmp['ts_code'] == '300330.SZ']['totals1'])
#final_df_tmp = pd.merge(final_df,final_source_df,on=['trade_date','ts_code'],how='left')
daily_stocks_tmp.drop(['total_share_x','pre_close_x','total_share_y','pre_close_y'],axis=1,inplace=True)
print("2 daily_stocks_tmp['totals1'] \n")
print(daily_stocks_tmp[daily_stocks_tmp['ts_code'] == '300330.SZ']['totals1'])
#final_df_tmp.drop(['total_share_x','pre_close_x','total_share_y','pre_close_y'],axis=1,inplace=True)

#如果daily_stocks_tmp没问题就 给 daily_stocks
daily_stocks = daily_stocks_tmp

#添加上市时间信息 以及筛选
#info_df = pd.read_csv('F:/SmartLab/量化投资/version2.0/version2.0/code/stock_info_1007.csv')
info_df = data
daily_stocks = pd.merge(daily_stocks,info_df,on=['ts_code'],how='left')
print("3 daily_stocks['totals1'] \n")
print(daily_stocks[daily_stocks['ts_code'] == '300330.SZ']['totals1'])
#final_df = pd.merge(final_df,info_df,on=['ts_code'],how='left')
daily_stocks.list_date = pd.to_datetime(daily_stocks.list_date,format="%Y%m%d")
#final_df.list_date = pd.to_datetime(final_df.list_date,format="%Y%m%d")
daily_stocks.trade_date = pd.to_datetime(daily_stocks.trade_date,format="%Y-%m-%d")
#final_df.trade_date = pd.to_datetime(final_df.trade_date,format="%Y-%m-%d")
daily_stocks['period'] = daily_stocks.trade_date - daily_stocks.list_date
#final_df['period'] = final_df.trade_date - final_df.list_date
daily_stocks.period = daily_stocks.period.apply(lambda x:x.days)
#final_df.period = final_df.period.apply(lambda x:x.days)
daily_stocks_tmp = daily_stocks[daily_stocks['period']>270]  #选取上市日期大于9个月的
#final_df1 = final_df[final_df['period']>90]



#Turn different time format to the datetime[64]
def FormatTime(str_x):
    try:
        return pd.to_datetime(str_x,format="%Y%m%d")
    except ValueError:
        return pd.to_datetime(str_x)
    
#添加10大股东信息
top10_df = pd.read_csv(cur_dir_path+'/top10_1116.csv')
#top10_df.head()
#print("top10_df",top10_df)
'''
top10_df = pd.DataFrame()
print('top10',daily_stocks_tmp.columns)
for code in daily_stocks_tmp['ts_code'] :
    print(code)
    for day in daily_stocks_tmp[daily_stocks_tmp['ts_code'] == code]['datetime'] :
        end_time = FormatTime(day)
        beg_time =  end_time - datetime.timedelta(months=3)
        try:
            #获取股票code的十大股东
            time.sleep(0.1)
            df = pro.top10_holders(ts_code=code,start_date=beg_time,end_date=end_time)
        except:
            #如果获取数据超时，停0.2秒重新获取
            time.sleep(2)
            df = pro.top10_holders(ts_code=code,start_date=beg_time,end_date=end_time)
        if df.empty:
            continue
        #选取最新的几个股东求和hold_ratio
        df = df[df['ann_date'] == df.iloc[0,1]]
        df = df[df['end_date'] == df.iloc[0,2]]
        df = df.drop_duplicates(['holder_name'])
        df['hold_ratio'] = df['hold_ratio'].sum()
        df = df.drop_duplicates(['hold_ratio'])
        print(df['hold_ratio'],daily_stocks_tmp['ts_code'])
        daily_stocks_tmp[daily_stocks_tmp['ts_code'] == code and daily_stocks_tmp['datetime'] == day]['top10sh'] = df['hold_ratio'] 
        df = df[['ts_code','hold_ratio']]
        #print(df)
        top10_df = pd.concat([top10_df,df])
        #print(top10_holders)
        #top10_holders.to_csv(stock_saved_path+'top10_1007.csv',index=False)
    
    
    
top10_df['top10_d_r'] = top10_df['hold_ratio']
'''
top10_df['ts_code'] = top10_df['ts_code'].apply(lambda x:int(x.replace('.SZ','').replace('.SH','')))

daily_stocks_tmp['ts_code'] = daily_stocks_tmp['ts_code'].apply(lambda x:int(x.replace('.SZ','').replace('.SH','')))

#final_df1['ts_code'] = final_df1['ts_code'].apply(lambda x:int(x.replace('.SZ','').replace('.SH','')))

daily_stocks_tmp = pd.merge(daily_stocks_tmp,top10_df,on=['ts_code'],how='left')
print("4 daily_stocks_tmp['totals1'] \n")
print(daily_stocks_tmp[daily_stocks_tmp['ts_code'] == 300330]['totals1'])
#final_df1 = pd.merge(final_df1,top10_df,on=['ts_code'],how='left')
daily_stocks_tmp['day_tomo'] = daily_stocks_tmp['day_tomo'].apply(lambda x:(str(x).replace('.0','')))
#final_df1['day_tomo'] = final_df1['day_tomo'].apply(lambda x:(str(x).replace('.0','')))
daily_stocks_tmp['day_tomo'] = daily_stocks_tmp['day_tomo'].apply(lambda x:FormatTime(x))
#final_df1['day_tomo'] = final_df1['day_tomo'].apply(lambda x:FormatTime(x))
daily_stocks_tmp['day_aftertomo'] = daily_stocks_tmp['day_aftertomo'].apply(lambda x:(str(x).replace('.0','')))
#final_df1['day_aftertomo'] = final_df1['day_aftertomo'].apply(lambda x:(str(x).replace('.0','')))
daily_stocks_tmp['day_aftertomo'] = daily_stocks_tmp['day_aftertomo'].apply(lambda x:FormatTime(x))
#final_df1['day_aftertomo'] = final_df1['day_aftertomo'].apply(lambda x:FormatTime(x))
daily_stocks_tmp['after_sign'] = daily_stocks_tmp['after_sign'].astype(int)
#final_df1['after_sign'] = final_df1['after_sign'].astype(int)

print("daily_stocks_tmp['hold_ratio']",daily_stocks_tmp['hold_ratio'])
#修改列名
daily_stocks_tmp.rename(columns={'trade_date':'datetime','ts_code':'code','mean_price':'mean_value4_before','close1':'settlement',\
                          'mean_price_hl':'mean_value2_hl_before','hold_ratio':'top10sh','mean_price_oc':'mean_value_oc_before'},inplace=True)
daily_stocks_tmp.rename(columns={'close_highest':'30_close_highest','cp_sum_five':'cp_sum'},inplace=True)
daily_stocks_tmp['cq_sign'] = 0

#手动调参代码
#final_use = final_daily_stocks
final_use = daily_stocks_tmp[['datetime','code','totals1','policy3','open','high','mean_value2_hl_before','policy1','policy2','tr_before',\
                     'settlement','30_close_highest','mean_value4_before','low','top10sh','after_sign','day_tomo',\
                     'day_aftertomo','cp_sum','cq_sign','mean_value_oc_before','close','h_l_diff']]


#得到输入的股票形式
#final_use = final_df1[['datetime','code','day_tomo','day_aftertomo','30_close_highest','after_sign','cp_sum','high','low','mean_value2_hl_before',\
#                       'mean_value2_hl_before','mean_value_oc_before','open','policy1','policy2','policy3',\
#                     'settlement','top10sh','totals1','tr_before','close']]

#删除多余日期的股票
final_use = final_use[final_use['datetime']>= pd.to_datetime(start_date_rel,format="%Y%m%d")]
print("6 final_use['totals1'] \n")
print(final_use[final_use['code'] == 300330]['totals1'])
#保存文件
daily_stocks_tmp.to_csv(daily_path + '0101_1001_daily_change_columns.csv',index=False)  
#final_df1.to_csv(daily_path + '0101_0110_daily_change_columns.csv',index=False)
watch_df = final_use.head()

#最终版复权后所有股票日线数据
final_use.to_csv(final_save_path+'daily_stocks.csv',index=False)

'''
#处理复权因子
fq_stocks['trade_date'] = pd.to_datetime(fq_stocks['trade_date'])
#fq_final_df['trade_date'] = pd.to_datetime(fq_final_df['trade_date'])
fq_stocks_use = fq_stocks[fq_stocks['trade_date']>= pd.to_datetime(start_date_rel,format="%Y%m%d")]
#fq_final_use = fq_final_df[fq_final_df['trade_date']>= pd.to_datetime(start_date1,format="%Y%m%d")]
fq_stocks_use['factor_rate'] = 1
#fq_final_use['factor_rate'] = 1

fq_tmp_final = pd.DataFrame()

#若股票有除权操作 则重新计算factor_rate
for code in np.unique(fq_stocks_use['ts_code']):
    if code in cq_stocks_list:
        tmp_df1 = fq_stocks_use[fq_stocks_use['ts_code'] == code]
        fq_stocks_use = fq_stocks_use[fq_stocks_use['ts_code'] != code]
        tmp_df1.reset_index(inplace=True)
        new_factor = tmp_df1.loc[0,'adj_factor']
        tmp_df1['factor_rate'] = tmp_df1['adj_factor']/new_factor
        fq_tmp_final = pd.concat([fq_tmp_final,tmp_df1])
    else:
        continue
    
fq_tmp_final.drop(['index'],axis=1,inplace=True)
fq_stocks_use = pd.concat([fq_stocks_use,fq_tmp_final])
print('将所有股票的复权因子保存到一个文件中')
fq_stocks_use.to_csv(final_save_path+'fq_factor.csv',index=False)
'''