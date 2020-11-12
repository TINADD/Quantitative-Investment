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


#给定下载日期，比如要测试19年11月到现在的数据，需要从19年10月开始下载
#获取20191101-20200620之间的股票数据
#获取20200101-20200630之间的股票数据
#获取20200101-20201001之间的股票数据[0101,1001)
start_date_bef = '20191201' #从当前日期开始下载
start_date_rel = '20200101' #实际需要的起始日期
end_date = '20201001' #实际的要获取股票数据的结束日期,获取结果不含该日期

saved_path = 'E:/Stock/version2.0/dataDownload/'+start_date_rel+'_'+end_date+'/' #当前程序下载的所有文件都存在此目录下
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

for code in data['ts_code']:
    if code in Get_info_list:
        continue
    elif os.path.exists(single_path + code + '.csv') and os.path.getsize(single_path + code + '.csv')>1000:
            print('股票日线数据已存在',code)
            #continue
    else:
        pass
    print ('当前股票代码==',code)
    try:
        #获取股票代码==code的在[start_date,end_date]的日线数据
        code_df = pro.daily(ts_code=code, start_date=start_date_bef, end_date=end_date)
    except:
        #如果获取数据超时，停0.2秒重新获取
        time.sleep(0.2)
        code_df = pro.daily(ts_code=code, start_date=start_date_bef, end_date=end_date)

    #add turnover info 增加换手率信息
    try:
        tr_df = pro.daily_basic(ts_code=code, start_date=start_date_bef, end_date=end_date, fields='ts_code,trade_date,turnover_rate,total_share')
    except:
        time.sleep(0.2)
        tr_df = pro.daily_basic(ts_code=code, start_date=start_date_bef, end_date=end_date, fields='ts_code,trade_date,turnover_rate,total_share')

    #合并上面获取的单只股票的日线数据    
    code_df = pd.merge(code_df,tr_df,how='left',on=['trade_date','ts_code'])
    #将code股票的未复权的日线数据存到对应的文件中
    code_df.to_csv(single_path_source + code + '.csv')
    
    daily_stocks_source = pd.concat([daily_stocks_source,code_df])
    #如果除权 则对日线价格进行复权处理
    try:
        fq_df = pro.adj_factor(ts_code=code, start_date=start_date_bef, end_date=end_date)
    except:
        time.sleep(0.2)
        fq_df = pro.adj_factor(ts_code=code, start_date=start_date_bef, end_date=end_date)
    fq_df.to_csv(fq_path + code + '.csv')

    fq_df = fq_df[fq_df['trade_date']>=start_date_bef]
    fq_df = fq_df[fq_df['trade_date']<=end_date]
    
    fq_stocks = pd.concat([fq_stocks,fq_df])
    try:
        tmp_min = min(fq_df['adj_factor'])
    except ValueError:
        error_list.append(code)
        continue
    tmp_max = max(fq_df['adj_factor'])
    if tmp_min == tmp_max:  #code股票不需要除权操作
        pass
    else:
        cq_stocks_list.append(code)
        try:
            fq_df['New_factor'] = fq_df.loc[0,'adj_factor']
        except KeyError:
            error_list.append(code)
            continue
        fq_df['factor_rate'] = fq_df['adj_factor']/fq_df['New_factor']
        fq_df.drop(['adj_factor','New_factor'],axis=1,inplace=True)
        fq_df['trade_date'] = pd.to_datetime(fq_df['trade_date'],format="%Y%m%d")

        code_df['trade_date'] = pd.to_datetime(code_df['trade_date'])
        code_df = pd.merge(code_df,fq_df,on=['ts_code','trade_date'],how='left')
        code_df['close'] = code_df['close'] * code_df['factor_rate']
        code_df['open'] = code_df['open'] * code_df['factor_rate']
        code_df['high'] = code_df['high'] * code_df['factor_rate']
        code_df['low'] = code_df['low'] * code_df['factor_rate']
        #增加对成交量的复权处理
        code_df['vol'] = code_df['vol'] / code_df['factor_rate']
    
    #前12个交易日涨幅 前5个交易日的成交量
    for i in range(1,13):
        code_df['cp' + str(i)] = code_df['pct_chg'].shift(-i)
    for j in range(1,6):
        code_df['vol' + str(j)] = code_df['vol'].shift(-j)
    code_df['cp_count_s'] = (code_df['cp1']>0).astype(int) + (code_df['cp2']>0).astype(int) + (code_df['cp3']>0).astype(int) + (code_df['cp4']>0).astype(int) + (code_df['cp5']>0).astype(int)
    code_df['cp_count_s'].describe()
    
     #前12个交易日的涨幅之和 和 涨幅为正的个数
    code_df['cp_count_l'] = 0
    code_df['cp_sum_twe'] = 0
    
    for i in range(1,13):
        code_df['cp_count_l'] = code_df['cp_count_l'] + (code_df['cp' + str(i)]>0).astype(int)
        code_df['cp_sum_twe'] = code_df['cp_sum_twe'] + code_df['cp'+str(i)]
    #更改五日涨幅的指标
    code_df['cp_sum_five'] = 0
    for j in range(1,6):
        code_df['cp_sum_five'] = code_df['cp_sum_five'] + code_df['cp'+str(j)]
        
    #后两个交易日
    code_df['day_tomo'] = code_df['trade_date'].shift(1)
    code_df['day_aftertomo'] = code_df['trade_date'].shift(2)
    #code_df['tr_choose'] = code_df['turnover_rate'].shift(-1)
    
    #选股当天的换手率
    code_df['tr_before'] = code_df['turnover_rate'].shift(-1)
    
    #前两天最高 前三天收盘 得到policy3
    code_df['high1'] = code_df['high'].shift(-1)
    code_df['high2'] = code_df['high'].shift(-2)
    code_df['close1'] = code_df['close'].shift(-1)
    code_df['close2'] = code_df['close'].shift(-2)
    code_df['close3'] = code_df['close'].shift(-3)
    code_df['ch1'] = (code_df['high1'] - code_df['close2'])/code_df['close2']
    code_df['ch2'] = (code_df['high2'] - code_df['close3'])/code_df['close3']
    code_df['policy3'] = code_df['ch1'] + code_df['ch2']
    
#    #新增涨幅指标
#    code_df['open1'] = code_df['open'].shift(-1)
#    code_df['open2'] = code_df['open'].shift(-2)
#    code_df['open3'] = code_df['open'].shift(-3)
#    code_df['open4'] = code_df['open'].shift(-4)
#    code_df['open5'] = code_df['open'].shift(-5)
#    #print ([zip(code_df['open1'],code_df['open2'],code_df['open3'],code_df['open4'],code_df['open5'])])
##    code_df['open_list'] = [zip(code_df['open1'],code_df['open2'],code_df['open3'],code_df['open4'],code_df['open5'])]
##    for j in range(2,6):
##        code_df['min_open'] = min(code_df['min_open'],code_df['open'+str(j)])
##    code_df['min_open'] = code_df['open_list'].apply(lambda x:min(x))
#    tmp_code_df = code_df[['open1','open2','open3','open4','open5']]
#    tmp_code_df['min_open'] = tmp_code_df.min(axis=1)
#    code_df['min_open'] = tmp_code_df['min_open']
#    code_df['cp_sum_five'] = ((code_df['close1'] - code_df['min_open'])/code_df['min_open'])*100
    
    #前30天最高价
    try:
        code_df['trade_date'] = code_df['trade_date'].apply(lambda x:datetime.datetime.strptime(x,'%Y%m%d'))
    except:
        pass
    code_df['close_highest'] = 0
    #code_df['highest'] = 0
    code_df['close_lowest'] = 0
    '''
    #原来获取最高价的方式-通过时间来判断
    for i in range(0,code_df.shape[0]-22,1):
        tmp_start = (code_df.ix[i,'trade_date'] - datetime.timedelta(days=30)).strftime('%Y%m%d')
        #tmp_start = (code_df.loc[i,'trade_date'] - datetime.timedelta(days=14))
        tmp_end = code_df.loc[i,'trade_date']
#        print (tmp_start)
#        print (tmp_end)
        tmp_df = code_df[tmp_start<=code_df['trade_date']]
        tmp_df = tmp_df[tmp_end>tmp_df['trade_date']]
        #print (tmp_df[['trade_date','close']])
        try:
            code_df.loc[i,'close_highest'] = max(tmp_df['close'])
        except ValueError:
            code_df.loc[i,'close_highest'] = np.nan
    '''
    for i in range(0,code_df.shape[0]-22,1):
        tmp_df = code_df[(i+1):(i+23)]
        try:
            code_df.loc[i,'close_highest'] = max(tmp_df['close'])
        except ValueError:
            code_df.loc[i,'close_highest'] = np.nan
        try:
            code_df.loc[i,'close_lowest'] = min(tmp_df['close'])
        except ValueError:
            code_df.loc[i,'close_lowest'] = np.nan
            
#        #最低/最高的最低/最高价格
#        try:
#            code_df.loc[i,'highest'] = max(tmp_df['high'])
#        except ValueError:
#            code_df.loc[i,'highest'] = np.nan
#        try:
#            code_df.loc[i,'lowest'] = min(tmp_df['low'])
#        except ValueError:
#            code_df.loc[i,'lowest'] = np.nan
        
    code_df['policy1'] = (code_df['close_highest'] - code_df['close1'])/code_df['close1']
        
    code_df['policy2'] = code_df['vol1']/code_df['vol2']
    
    code_df['cp_count_s'] = (code_df['cp1']>0).astype(int) + (code_df['cp2']>0).astype(int) + (code_df['cp3']>0).astype(int) + (code_df['cp4']>0).astype(int) + (code_df['cp5']>0).astype(int)
    code_df['cp_count_s'].describe()
    
     #前12个交易日的涨幅之和 和 涨幅为正的个数
    code_df['cp_count_l'] = 0
    code_df['cp_sum_twe'] = 0
    
    for i in range(1,13):
        code_df['cp_count_l'] = code_df['cp_count_l'] + (code_df['cp' + str(i)]>0).astype(int)
        code_df['cp_sum_twe'] = code_df['cp_sum_twe'] + code_df['cp'+str(i)]
#    code_df['cp_sum_five'] = 0
#    code_df['cp_sum_five'] = code_df['cp1'] + code_df['cp2'] + code_df['cp3'] + code_df['cp4'] + code_df['cp5']
        
    try:
        code_df.drop(['cp_sum'],axis=1,inplace=True)
        code_df.drop(['Unnamed: 0'],axis=1,inplace=True)
    except:
        pass
    
    #计算不同方式计算的均价
    code_df['amount1'] = code_df['amount'].shift(-1)
    code_df['low1'] = code_df['low'].shift(-1)
    code_df['open1'] = code_df['open'].shift(-1)
    code_df['mean_price'] = (code_df['amount1']/code_df['vol1'])*10
    code_df['mean_price_hl'] = (code_df['high1'] + code_df['low1'])/2
    code_df['mean_price_oc'] = (code_df['open1'] + code_df['close1'])/2
    code_df['mean_sig'] = code_df['mean_price']/code_df['high1']
    
    #得到卖出当天是否会开盘涨停的信息
    code_df['high_tomo'] = code_df['high'].shift(1)
    code_df['low_tomo'] = code_df['low'].shift(1)
    code_df['after_sign'] = (code_df['high_tomo'] == code_df['low_tomo'])
    code_df['h_l_diff'] = (code_df['close_highest'] - code_df['close_lowest'])/code_df['close_lowest']
    
    #将单只复权后的股票存到对应的路径
    code_df.to_csv(single_path + code + '.csv')

    daily_stocks = pd.concat([daily_stocks,code_df])
    #final_df = pd.concat([final_df,code_df])
    Get_info_list.append(code)
    time.sleep(1)
    
print('将所有股票的日线数据保存到一个文件中')    
#保存初次合成结果
daily_stocks.to_csv(daily_path + 'tmpDaily.csv') #复权后
#final_df.to_csv(daily_path + 'source_daily.csv')
daily_stocks_source.to_csv(single_path_source + 'tmpDailySource.csv') #未复权
#final_source_df.to_csv(single_path_source + 'source_daily.csv')

'''注意已经有原始价格了，不需要再下载一次了，直接对final_source_df和final_df进行操作。需补上这段代码。'''
#总市值信息
daily_stocks_source = daily_stocks_source[['trade_date','ts_code','total_share','pre_close']]
#final_source_df = final_source_df[['trade_date','ts_code','total_share','pre_close']]
daily_stocks_source['totals1'] = daily_stocks_source['total_share']*daily_stocks_source['pre_close']
#final_source_df['totals1'] = final_source_df['total_share']*final_source_df['pre_close']
daily_stocks_source['trade_date'] = pd.to_datetime(daily_stocks_source['trade_date'])
#final_source_df['trade_date'] = pd.to_datetime(final_source_df['trade_date'])
daily_stocks_tmp = pd.merge(daily_stocks,daily_stocks_source,on=['trade_date','ts_code'],how='left')
#final_df_tmp = pd.merge(final_df,final_source_df,on=['trade_date','ts_code'],how='left')
daily_stocks_tmp.drop(['total_share_x','pre_close_x','total_share_y','pre_close_y'],axis=1,inplace=True)

#final_df_tmp.drop(['total_share_x','pre_close_x','total_share_y','pre_close_y'],axis=1,inplace=True)

#如果daily_stocks_tmp没问题就 给 daily_stocks
daily_stocks = daily_stocks_tmp


#添加上市时间信息 以及筛选
info_df = pd.read_csv('stock_info_1007.csv')
daily_stocks = pd.merge(daily_stocks,info_df,on=['ts_code'],how='left')
#final_df = pd.merge(final_df,info_df,on=['ts_code'],how='left')
daily_stocks.list_date = pd.to_datetime(daily_stocks.list_date,format="%Y%m%d")
#final_df.list_date = pd.to_datetime(final_df.list_date,format="%Y%m%d")
daily_stocks.trade_date = pd.to_datetime(daily_stocks.trade_date,format="%Y-%m-%d")
#final_df.trade_date = pd.to_datetime(final_df.trade_date,format="%Y-%m-%d")
daily_stocks['period'] = daily_stocks.trade_date - daily_stocks.list_date
#final_df['period'] = final_df.trade_date - final_df.list_date
daily_stocks.period = daily_stocks.period.apply(lambda x:x.days)
#final_df.period = final_df.period.apply(lambda x:x.days)
daily_stocks_tmp = daily_stocks[daily_stocks['period']>90]  #选取上市日期大于3个月的
#final_df1 = final_df[final_df['period']>90]



##添加总市值信息
#totals_df = pd.read_csv('D:/Stock/code/stock_info.csv')
#final_df1['ts_code'] = final_df1['ts_code'].apply(lambda x:int(x.replace('.SZ','').replace('.SH','')))
#totals_df = totals_df[['code','totals']]
#totals_df.rename(columns={'code':'ts_code'},inplace=True)
#final_df1 = pd.merge(final_df1,totals_df,on=['ts_code'],how='left')
#final_df1['totals1'] = final_df1['totals'] * final_df1['close1']
#final_df1['totals1'].describe()

#Turn different time format to the datetime[64]
def FormatTime(str_x):
    try:
        return pd.to_datetime(str_x,format="%Y%m%d")
    except ValueError:
        return pd.to_datetime(str_x)
    
#添加10大股东信息
top10_df = pd.read_csv('top10_1007.csv')
#top10_df.head()

top10_df['ts_code'] = top10_df['ts_code'].apply(lambda x:int(x.replace('.SZ','').replace('.SH','')))
daily_stocks_tmp['ts_code'] = daily_stocks_tmp['ts_code'].apply(lambda x:int(x.replace('.SZ','').replace('.SH','')))
#final_df1['ts_code'] = final_df1['ts_code'].apply(lambda x:int(x.replace('.SZ','').replace('.SH','')))

daily_stocks_tmp = pd.merge(daily_stocks_tmp,top10_df,on=['ts_code'],how='left')
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

#保存文件
daily_stocks_tmp.to_csv(daily_path + '0101_1001_daily_change_columns.csv',index=False)  
#final_df1.to_csv(daily_path + '0101_0110_daily_change_columns.csv',index=False)
watch_df = final_use.head()

#最终版复权后所有股票日线数据
final_use.to_csv(final_save_path+'daily_stocks.csv',index=False)

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
