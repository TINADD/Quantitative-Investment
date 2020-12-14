#pandas处理日期，按照日期筛选
import pandas as pd
import os

#20201101-20201201
#20200101-20200201
start_date = '20200101'
end_date = '20200201'

start_date_format = pd.to_datetime(start_date)
end_date_format = pd.to_datetime(end_date)

data_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))+'/stockdata/'+start_date+'_'+end_date+'/'
fenshi_data_path =  os.path.abspath(os.path.dirname(os.path.dirname(__file__)))+'/stockdata/20200101_'+'20201001/'
daily_path = data_path + "1214-daily20200101-20201206.csv"
fenshi_path = fenshi_data_path + "fenshi_after_fq_0101_1001.csv"

new_daily_path = data_path + '1214-daily20200101_20200201.csv'
new_fenshi_path = data_path + "1214-fenshi20200101_20200201.csv"

'''
#读文件
daily_df = pd.read_csv(daily_path)

#整理数据
#将数据类型转换为日期类型

daily_df['datetime'] = pd.to_datetime(daily_df['datetime'])
con1 = daily_df['datetime']>=start_date_format
con2 = daily_df['datetime']<=end_date_format

new_daily_df = daily_df[con1 & con2]
new_daily_df.to_csv(new_daily_path,index=False)

'''

fenshi_df = pd.read_csv(fenshi_path)
fenshi_df['date'] = pd.to_datetime(fenshi_df['date'])
con1 = fenshi_df['date']>=start_date_format
con2 = fenshi_df['date']<=end_date_format

new_fenshi_df = fenshi_df[con1 & con2]
new_fenshi_df.to_csv(new_fenshi_path,index=False)
