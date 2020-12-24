import sys
import os
import tushare as ts
import pandas as pd
import datetime
import time
import configparser

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
pro = ts.pro_api()

today = '20201218'
today_before = '20201018'

data_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))+'/stockdata/'
mkdir(data_path)

top10_path = data_path + 'top10.csv'
saved_daily_path = data_path + today + '_daily.csv'
#获得交易日历
trade_cal_df = pro.trade_cal(exchange='',start_date=today_before,end_date=today)
trade_cal_df = trade_cal_df[trade_cal_df['is_open'] == 1]
#print(trade_cal_df['cal_date'][0])
test = trade_cal_df['cal_date'].values.tolist()
#print(test)
today = test[-1]
today_before = test[-22]
#print(today)
#print(today_before)
#print(trade_cal_df['cal_date']) #输出[start,end]的交易数据

def get_day_daily():
    try:
        stock_basic = pro.stock_basic(exchange_id='', is_hs='', fields='ts_code,symbol,name,list_date,list_status')
        #得到非ST股票
        stock_basic['st_sig'] = stock_basic['name'].apply(lambda x:1 if x.startswith('ST') else 0)
        stock_basic = stock_basic[stock_basic['st_sig']==0]
            
        code_df = pd.DataFrame()
        count = 0
        for code in stock_basic['ts_code']:
            print (code)
            #频繁获取 会导致堵塞
            count += 1
            #得到前复权的日线数据
            try:
                tmp_df = ts.pro_bar(ts_code=code, adj='qfq', start_date=today_before, end_date=today,factors=['tor'])#提取前复权必须输入code
            except:
                time.sleep(0.5)
                tmp_df = ts.pro_bar(ts_code=code, adj='qfq', start_date=today_before, end_date=today,factors=['tor'])
            #print(tmp_df)    
            code_df = pd.concat([code_df,tmp_df])   
        #print('code_df',code_df)
        #计算平均价格
        #amount:总市值；vol：成交量
        code_df['mean_price'] = code_df['amount']*10/code_df['vol']
        trade_day = code_df.index[0]
        
        #print('mean_price')
        #print(code_df['mean_price'])    
        #获取股票的基本信息， 所属行业/上市日期 由上市日期得到股票上市的天数
        data_info_df = pro.stock_basic(exchange='', list_status='L', fields='ts_code,industry,list_date')
        data_info_df['trade_date'] = today
        data_info_df['trade_date'] = data_info_df['trade_date'].apply(lambda x:datetime.datetime.strptime(x,"%Y%m%d"))
        data_info_df['list_date'] = data_info_df['list_date'].apply(lambda x:datetime.datetime.strptime(x,"%Y%m%d"))
        data_info_df['PeriodToMar'] = data_info_df['trade_date'] - data_info_df['list_date']
        data_info_df['PeriodToMar'] = data_info_df['PeriodToMar'].apply(lambda x:x.days)
            
        #截取上市天数>270天的股票
        data_info_df = data_info_df[data_info_df['PeriodToMar'] > 270]
        data_info_df = data_info_df[['ts_code','industry','list_date']]
        #print('data_info_df')
        #print(data_info_df['ts_code'])   
        #得到十大股东的信息
        #top10.csv ts_code:0000001.SZ hold_ratio:67.97 top10_d_r:67.97
        top10_info_df = pd.read_csv(top10_path)
        top10_info_df.rename(columns={'top10sh':'hold_ratio'},inplace=True) #inplace=True 在视图上更新
        #print('top10')
        
        #print(top10_info_df)
        #得到总股本
        totals_df = pro.daily_basic(ts_code='', trade_date=today, fields='ts_code,total_share')
        if totals_df.shape[0] == 0:
            totals_df = pro.daily_basic(ts_code='', trade_date=trade_day, fields='ts_code,total_share')
        else:
            pass
        if totals_df.shape[0] == 0:
            print ('Error')
            return 0
        #print('totals_df')
        #print(totals_df)    
        
        #print('code_df-1')
        #print(code_df)
        code_df = pd.merge(data_info_df,code_df,how='left',on=['ts_code'])
        #print('code_df-2')
        #print(code_df)
        code_df = pd.merge(code_df,totals_df,how='left',on=['ts_code'])
        #print('code_df-3')
        #print(code_df)
        #code_df.rename(columns={'ts_code':'code'},inplace=True)
        #print('code_df1')
        #print(code_df)

        #print('code_df')
        #print(code_df)

        code_df = pd.merge(code_df,top10_info_df,how='left',on=['ts_code'])    
        #print('code_df-4')
        #print(code_df)
        code_df.dropna(how='any',inplace=True)
        
        code_df['ts_code'] = code_df['ts_code'].apply(lambda x:int(x.replace('.SH','').replace('.SZ','')))     
        #得到总市值信息
        code_df['totals_mv'] = code_df['close']*code_df['total_share']
        code_df['totals_mv'] = code_df['totals_mv']/10000
        code_df['mean_price'] = code_df['amount']*10/code_df['vol']
        code_df['trade_date'] = code_df['trade_date'].apply(lambda x:datetime.datetime.strptime(str(x),"%Y%m%d"))
        #code_df['list_date'] = code_df['list_date'].apply(lambda x:datetime.datetime.strptime(x,"%Y%m%d"))
        code_df['PeriodToMar'] = code_df['trade_date'] - code_df['list_date']
        code_df['PeriodToMar'] = code_df['PeriodToMar'].apply(lambda x:x.days)
        code_df['cq_sign'] = 0
       
        #筛选股票
        code_df = code_df.loc[(code_df['ts_code']<688000 )| (code_df['ts_code'] >=689000)]
        code_df = code_df[['trade_date','ts_code','open','high','close','pre_close','vol','mean_price','amount','pct_chg','turnover_rate','hold_ratio',\
                               'top10_d_r','industry','totals_mv','PeriodToMar','cq_sign']]
        code_df.dropna(how='any',inplace=True)
        print('有交易写文件')
        code_df.to_csv(saved_daily_path,encoding='utf-8',index=False)
        return 1
    except Exception as ex:
        print('异常',ex)
        return 0

start_time = time.perf_counter()
get_day_daily()
end_time = time.perf_counter()
print("下载数据用时%.2f秒"%(end_time-start_time))
