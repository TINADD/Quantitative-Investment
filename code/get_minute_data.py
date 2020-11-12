# -*- coding: utf-8 -*-
"""
Created on Wed Mar  6 20:53:15 2019
Get lastest minute data.
No fq.

@author: PC
"""

import sys
import os
#dirname, filename = os.path.split(os.path.abspath(sys.argv[0])) 
#print (os.path.realpath(sys.argv[0]))
#print (os.getcwd())
#sys.path.append(dirname)
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

'''
Function---GetMinuteData
Get the minute data from start_date to end_date.
And save files in the specific path.
Files include one whole file to use finally and files of different data stocks.
'''

token = '92fa5b4defcb65d71defd90b46b240ad77860cc3c0ec0958e492172d'
#获取2020-05-01到2020-06-30的分时数据
#获取2020-01-01到2020-10-01的分时数据
start_date1 = '20201001'
end_date1 = '20201101'
path = 'E:/Stock/version2.0/dataDownload/'+start_date1+'_'+end_date1+'/fenshi/' #当前程序下载的所有文件都存在此目录下

mkdir(path)

ts.set_token(token)
pro = ts.pro_api()
#Final whole file path and name
final_save_path = path + 'fenshi_'+start_date1 + '_'+ end_date1 + '.csv'
single_path = path + 'stockSingle/'
mkdir(single_path)

#Get lastest trading date -- date_list and save it in date_df.cal_date
end_date2 = (datetime.datetime.strptime(end_date1,'%Y%m%d') +  datetime.timedelta(days=1)).strftime('%Y%m%d')
print('获取交易日历')
#获取各大交易所交易日历数据，默认上交所
#输出交易日期
date_df = pro.trade_cal(exchange='', start_date=start_date1, end_date=end_date2)
#过滤掉不交易日期
date_df = date_df[date_df.is_open==1]
date_list = list(date_df.cal_date)
print ('股票交易日期数据：')
print (date_list)
#time.sleep(2)

#Get trading stocks
data = pro.stock_basic(exchange_id='', is_hs='', fields='ts_code,symbol,name,list_date,list_status')
#Save the stock id if it has got the minute data.
Get_info_list = []
#Save the final stock minute info.
final_df = pd.DataFrame()
result = []
log = 'log.txt'
tmp_data = pd.DataFrame()
for code in data['ts_code']:
    try:
        code_df = pd.DataFrame()
        if code in Get_info_list:
            continue
        elif os.path.exists(single_path + code + '.csv') and os.path.getsize(single_path + code + '.csv')>10000:
            print('股票分时数据已存在',code)
            tmp_df = pd.read_csv(single_path + code + '.csv');
            code_df = pd.concat([code_df,tmp_df]);
            code_df['trade_time'] = pd.to_datetime(code_df['trade_time'])
            code_df['date'] = code_df['trade_time'].apply(lambda x:x.date())
            code_df['time'] = code_df['trade_time'].apply(lambda x:x.time())
            date_num = len(np.unique(code_df['date']))
            tmp_list = [code,date_num]
            result.append(tmp_list)
            code_df.time = code_df.time.astype(str)
            code_df = code_df[code_df.time<='11:00:00']
            code_df = code_df[['trade_time','ts_code','open','close','high','low','date','time']]
            final_df = pd.concat([final_df,code_df])
            Get_info_list.append(code)
            #time.sleep(2)
            continue
        #print (code)

        for i in range(0,len(date_list)-1):
            time.sleep(0.1)
            try:
                #获取分时数据
                tmp_df = ts.pro_bar(ts_code=code, start_date=date_list[i], end_date=date_list[i+1], freq='1min')
            except:
                time.sleep(1)
                tmp_df = ts.pro_bar(ts_code=code, start_date=date_list[i], end_date=date_list[i+1], freq='1min')
            code_df = pd.concat([code_df,tmp_df])
            tmp_data = code_df
        #date_list中最后一天
        try:
            tmp_df = ts.pro_bar(ts_code=code, start_date=date_list[-1], end_date=end_date1, freq='1min')
        except:
            time.sleep(1)
            tmp_df = ts.pro_bar(ts_code=code, start_date=date_list[-1], end_date=end_date1, freq='1min')
        code_df = pd.concat([code_df,tmp_df])  
        tmp_data = code_df
        code_df.to_csv(single_path + code + '.csv')
        code_df['trade_time'] = pd.to_datetime(code_df['trade_time'])
        code_df['date'] = code_df['trade_time'].apply(lambda x:x.date())
        code_df['time'] = code_df['trade_time'].apply(lambda x:x.time())
        print('date:',code_df['date'])
        print('time:',code_df['time'])
        date_num = len(np.unique(code_df['date']))
        tmp_list = [code,date_num]
        result.append(tmp_list)
        code_df.time = code_df.time.astype(str)
        code_df = code_df[code_df.time<='11:00:00']
        code_df = code_df[['trade_time','ts_code','open','close','high','low','date','time']]
        final_df = pd.concat([final_df,code_df])
        Get_info_list.append(code)
        time.sleep(2)
    except:
        time.sleep(5)
        '''
        with open(log,'w') as f:
            f.write('异常出现')
            f.write(code)
            f.write(tmp_data)
        '''
        #print(code)
        #print ('Try Again!')
        code_df = pd.DataFrame()
        for i in range(0,len(date_list)-1):
            time.sleep(0.1)
            try:
                tmp_df = ts.pro_bar(ts_code=code, start_date=date_list[i], end_date=date_list[i+1], freq='1min')
            except:
                time.sleep(1)
                tmp_df = ts.pro_bar(ts_code=code, start_date=date_list[i], end_date=date_list[i+1], freq='1min')
            code_df = pd.concat([code_df,tmp_df])
        #date_list中最后一天
        try:
            tmp_df = ts.pro_bar(ts_code=code, start_date=date_list[-1], end_date=end_date1, freq='1min')
        except:
            time.sleep(1)
            tmp_df = ts.pro_bar(ts_code=code, start_date=date_list[-1], end_date=end_date1, freq='1min')
        code_df = pd.concat([code_df,tmp_df]) 
        print('在异常处理中重新获得分时数据')
        code_df.to_csv(single_path + code + '.csv')
        code_df['trade_time'] = pd.to_datetime(code_df['trade_time'])
        code_df['date'] = code_df['trade_time'].apply(lambda x:x.date())
        code_df['time'] = code_df['trade_time'].apply(lambda x:x.time())
        date_num = len(np.unique(code_df['date']))
        tmp_list = [code,date_num]
        result.append(tmp_list)
        code_df.time = code_df.time.astype(str)
        code_df = code_df[code_df.time<='11:00:00']
        code_df = code_df[['trade_time','ts_code','open','close','high','low','date','time']]
        final_df = pd.concat([final_df,code_df])
        Get_info_list.append(code)
        time.sleep(2)

print('将所有的股票数据保存到一个最终文件里')    
final_df.to_csv(final_save_path)
#fq_final_use = pd.read_csv('D:/Stock/Data/190101_190907/fq_factor.csv')
#final_df.head()
#fq_final_use.head()
#fq_final_use.drop(['adj_factor'],axis=1,inplace=True)
#fq_final_use.rename(columns={'trade_date':'date'},inplace=True)
#final_df.date = final_df.date.apply(lambda x:str(x))
#fenshi_final = pd.merge(final_df,fq_final_use,on=['ts_code','date'],how='left')
#fenshi_final['close'] = fenshi_final['close'] * fenshi_final['factor_rate']
#fenshi_final['open'] = fenshi_final['open'] * fenshi_final['factor_rate']
#fenshi_final['high'] = fenshi_final['high'] * fenshi_final['factor_rate']
#fenshi_final['low'] = fenshi_final['low'] * fenshi_final['factor_rate']
#fenshi_final.rename(columns={'trade_time':'datetime','ts_code':'code'},inplace=True)
#fenshi_final.drop(['factor_rate'],axis=1,inplace=True)
#fenshi_final['code'] = fenshi_final['code'].apply(lambda x:str(x).replace('.SZ','').replace('.SH',''))
#fenshi_final.to_csv('D:/Stock/Data/190101_190907/fenshi_stocks.csv',index=False)
