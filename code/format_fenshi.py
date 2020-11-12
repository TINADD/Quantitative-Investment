# -*- coding: utf-8 -*-
"""
Created on Sun Apr 28 10:07:28 2019
Get Jan-April fenshi data
already fq

@author: PC
"""
#拼接分时数据

import os
import pandas as pd
import numpy as np


def mkdir(path):
 
	folder = os.path.exists(path)
 
	if not folder:                   #判断是否存在文件夹如果不存在则创建为文件夹
		os.makedirs(path)            #makedirs 创建文件时如果路径不存在会创建这个路径
		print ("---  new folder...  ---")
		print ("---  OK  ---")
 
	else:
		print ("---  There is this folder!  ---")
#2020/01/01-2020/06/30
start_date = '2020-01-01'		
end_date = '2020-07-01'
fenshi_path = 'E:/Stock/my-version/data/fenshi_no_fq.csv'
#path1 = 'E:/Stock/Test/data/fenshi_test.csv'
#path2 = 'E:/Stock/Data/Fenshi20200109/20191221_20200109.csv'
#path3 = 'E:/Stock/Data/Fenshi20200111/20200110_20200111.csv'
final_save_path = 'E:/Stock/my-version/data/fenshi20200514已复权/'
mkdir(final_save_path)
print('读分时数据')
fenshi_df = pd.read_csv(fenshi_path)
'''
fenshi_df1 = pd.read_csv(path2)
fenshi_df2 = pd.read_csv(path3)

final_df = pd.concat ([final_df,fenshi_df1])

final_df = pd.concat ([final_df,fenshi_df2])
'''
#删掉列
print('部分分时数据,drop前',fenshi_df[0:10])
fenshi_df.drop(['Unnamed: 0'],axis=1,inplace=True)
print('部分分时数据，drop后',fenshi_df[0:10])

fenshi_df = fenshi_df[~fenshi_df['close'].isin(['close'])]
#测试分时数据里还有没有非法数据
error_data = fenshi_df[fenshi_df['open'] == 'open']
print('非法数据数量',len(error_data))
print('close',fenshi_df['close'])
print('读复权因子')
#分时数据进行复权处理
fq_final_use = pd.read_csv('E:/Stock/my-version/data/fq_factor.csv')
#head()函数的原型中，默认的参数size大小是 5，所以会返回 5 个数据。
print('分时数据前5行',fenshi_df.head())
print('复权因子前5行',fq_final_use.head())
fq_final_use.drop(['adj_factor'],axis=1,inplace=True)
fq_final_use.rename(columns={'trade_date':'date'},inplace=True)
fq_final_use['ts_code'] = fq_final_use['ts_code'].apply(lambda x:str(x).replace('.SZ','').replace('.SH',''))
fenshi_df['ts_code'] = fenshi_df['ts_code'].apply(lambda x:str(x).replace('.SZ','').replace('.SH',''))

#print('复权因子,合并前',fq_final_use['factor_rate'])
#print('合并前,分时',fenshi_df['ts_code'],fenshi_df['date'])
#print('合并前,复权因子',fq_final_use['ts_code'],fq_final_use['date'])

fenshi_final = pd.merge(fenshi_df,fq_final_use,on=['ts_code','date'],how='left')
#print('因子速率,合并后',fenshi_final['factor_rate'])
#print('合并后',fenshi_final['ts_code'],fenshi_final['date'])
fenshi_final = fenshi_final[fenshi_final['date']<end_date]
fenshi_final['close'] = fenshi_final['close'].astype('float64')
fenshi_final['close'] = fenshi_final['close'] * fenshi_final['factor_rate']
#字符串的原因
fenshi_final['open'] = fenshi_final['open'].astype('float64')
fenshi_final['open'] = fenshi_final['open'] * fenshi_final['factor_rate']
fenshi_final['high'] = fenshi_final['high'].astype('float64')
fenshi_final['high'] = fenshi_final['high'] * fenshi_final['factor_rate']
fenshi_final['low'] = fenshi_final['low'].astype('float64')
fenshi_final['low'] = fenshi_final['low'] * fenshi_final['factor_rate']
fenshi_final.rename(columns={'trade_time':'datetime','ts_code':'code'},inplace=True)
fenshi_final.drop(['factor_rate'],axis=1,inplace=True)
print('写最终文件')
fenshi_final.to_csv(final_save_path +'fenshi_stocks_fq.csv',index=False)

