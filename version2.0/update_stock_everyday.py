# -*- coding: utf-8 -*-
"""
Created on Mon Jul  8 00:13:16 2019

收盘之后下载今天的股票
属性包括
get config info from ini file
and no GUI
Return 1 if success else 0.
ANd judge if st or new stock.

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
import configparser

def update_data(token,path,level):
    
    ts.set_token(token)
    pro = ts.pro_api()
    
    today = time.strftime('%Y%m%d',time.localtime(time.time()))
    today_format = pd.to_datetime(today)
    #定义today后面两天
    today_after_2d_format = today_format+datetime.timedelta(days=2)
    today_after_2d_str = today_after_2d_format.strftime('%Y%m%d')
    #tomo = time.strftime('%Y%m%d',time.localtime(time.time()+172800))
    #从2019年11月1号开始下载数据
    #t = (2019,11,1,0,0,0,5,304,-1)
    #secs = time.mktime(t)
    #before = time.strftime('%Y%m%d',time.localtime(time.time()-secs))
    #before = '20191101'
    #下载前30天的数据 定义前30天
    today_before_30d_format = today_format-datetime.timedelta(days=30)
    today_before_30d_str = today_before_30d_format.strftime('%Y%m%d')


    #得到交易日历
    date_df = pro.trade_cal(exchange='', start_date=today_before_30d_str, end_date=today)
    #更新当天的十大股东占比
    top10_path = path+'top10.csv'
    #top10_df = pd.DataFrame()
    #top10_df = pd.read_csv(top10_path)
    #top10_df = top10_df.drop_duplicates(['ts_code'])
    #top10_df.to_csv('F:/top10.csv',index=False)
    stock_data = pro.stock_basic(exchange_id='', is_hs='', fields='ts_code,symbol,name,list_date,list_status')

    '''
    for code in stock_data['ts_code']:
        print(code)
        today_before_3m_format = today_format-datetime.timedelta(days=90)
        today_before_3m_str = today_before_3m_format.strftime('%Y%m%d')
        try:
            time.sleep(0.1)
            code_df = pro.top10_holders(ts_code=code,start_time=today_before_3m_str,end_time=today)
        except:
            time.sleep(0.2)
            code_df = pro.top10_holders(ts_code=code,start_time=today_before_3m_str,end_time=today)
        if code_df.empty:
            continue
        code_df = code_df[code_df['ann_date'] == code_df.iloc[0,1]]
        code_df = code_df[code_df['end_date'] == code_df.iloc[0,2]]
        code_df = code_df.drop_duplicates(['holder_name'])
        code_df['hold_ratio'] = code_df['hold_ratio'].sum()
        code_df = code_df.drop_duplicates(['holder_ratio'])
        code_df = code_df[['ts_code','hold_ratio']]
        top10_df = pd.concat([top10_df,code_df])
    
    top10_df['top_10_d_r'] = top10_df['hold_ratio']
    top10_df.to_csv(top10_path,index=False)
    '''
    print('开始update')
    #print(date_df)
    #判断今天是否交易
    try:
        print('开始判断',date_df.iloc[-1]['is_open'])
        #当天存在交易
        if (date_df.iloc[-1]['is_open'] == 1):
            print('有交易')
            top10_path = path + 'top10.csv'
            print (top10_path)
            df = pd.read_csv(top10_path)
            print (df.head())
            daily_path = path + 'daily_data.csv'
            
            #得到股票基础信息
            data = pro.stock_basic(exchange_id='', is_hs='',list_status='L', fields='ts_code,symbol,name,list_date,list_status')
            #得到非ST股票
            data['st_sig'] = data['name'].apply(lambda x:1 if x.startswith('ST') else 0)
            data = data[data['st_sig']==0]
            
            code_df = pd.DataFrame()
            count = 0
            
            for code in data['ts_code']:
                print ('有交易',code)
                #频繁获取 会导致堵塞
                count += 1
                if level > 1:
                    if count%190 == 0:
                        time.sleep(60)
                else:
                    pass
                
                #得到前复权的日线数据
                try:
                    tmp_df = ts.pro_bar(ts_code=code, adj='qfq', start_date=today_before_30d_str, end_date=today,factors=['tor'])
                except:
                    time.sleep(5)
                    tmp_df = ts.pro_bar(ts_code=code, adj='qfq', start_date=today_before_30d_str, end_date=today,factors=['tor'])
                #print(tmp_df)    
                code_df = pd.concat([code_df,tmp_df])
                
            #计算平均价格
            #amount:总市值；vol：成交量
            code_df['mean_price'] = code_df['amount']*10/code_df['vol']
            trade_day = code_df.index[0]
            
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
            
            #得到十大股东的信息
            top_info_df = pd.read_csv(top10_path)
            #得到总股本
            totals_df = pro.daily_basic(ts_code='', trade_date=today, fields='ts_code,total_share')
            if totals_df.shape[0] == 0:
                totals_df = pro.daily_basic(ts_code='', trade_date=trade_day, fields='ts_code,total_share')
            else:
                pass
            if totals_df.shape[0] == 0:
                print ('Error')
                return 0
            
            code_df = pd.merge(data_info_df,code_df,how='left',on=['ts_code'])
            code_df = pd.merge(code_df,totals_df,how='left',on=['ts_code'])
            code_df = pd.merge(code_df,top_info_df,how='left',on=['ts_code'])
            
            code_df.dropna(how='any',inplace=True)
            
            #得到总市值信息
            code_df['totals_mv'] = code_df['close']*code_df['total_share']
            code_df['totals_mv'] = code_df['totals_mv']/10000
            code_df['mean_price'] = code_df['amount']*10/code_df['vol'] #之前计算过了
            code_df['trade_date'] = code_df['trade_date'].apply(lambda x:datetime.datetime.strptime(str(x),"%Y%m%d"))
            #code_df['list_date'] = code_df['list_date'].apply(lambda x:datetime.datetime.strptime(x,"%Y%m%d"))
            code_df['PeriodToMar'] = code_df['trade_date'] - code_df['list_date']
            code_df['PeriodToMar'] = code_df['PeriodToMar'].apply(lambda x:x.days)
            code_df['cq_sign'] = 0
            code_df['ts_code'] = code_df['ts_code'].apply(lambda x:int(x.replace('.SH','').replace('.SZ','')))
            code_df = code_df[['trade_date','ts_code','open','high','close','pre_close','vol','mean_price','amount','pct_chg','turnover_rate','hold_ratio',\
                               'top10_d_r','industry','totals_mv','PeriodToMar','cq_sign']]
            code_df.dropna(how='any',inplace=True)
            print('有交易写文件')
            code_df.to_csv(daily_path,encoding='utf-8',index=False)
            return 1
        #当天不存在交易 比如周末才更新数据
        else:
            print('无交易')
            #获取前7天的交易日历
            today_before_7d_format = today_format-datetime.timedelta(days=7)
            today_before_7d_str = today_before_7d_format.strftime('%Y%m%d')
            df_test = pro.trade_cal(exchange='', start_date=today_before_7d_str, end_date=today)
            df_test = df_test[df_test['is_open']==1]
            list_test = list(df_test['cal_date'])
            today = list_test[-1]
            
            #today前18天
            #before = today-datetime.timedelta(days=18)
            today_before_18d_format = today_format-datetime.timedelta(days=18)
            today_before_18d_str = today_before_18d_format.strftime('%Y%m%d')
            top10_path = path + 'top10.csv'
            print (top10_path)
            df = pd.read_csv(top10_path)
            print (df.head())
            daily_path = path + 'daily_data.csv'
            
            data = pro.stock_basic(exchange_id='', is_hs='', fields='ts_code,symbol,name,list_date,list_status')
            data['st_sig'] = data['name'].apply(lambda x:1 if x.startswith('ST') else 0)
            data = data[data['st_sig']==0]
            code_df = pd.DataFrame()
            count = 0
            for code in data['ts_code']:
                #print ('无交易',code)
                count += 1
                if level > 1:
                    if count%190 == 0:
                        time.sleep(60)
                else:
                    pass
                try:
                    tmp_df = ts.pro_bar(ts_code=code, adj='qfq', start_date= today_before_18d_str , end_date=today,factors=['tor'])
                except:
                    time.sleep(5)
                    tmp_df = ts.pro_bar(ts_code=code, adj='qfq', start_date= today_before_18d_str , end_date=today,factors=['tor'])
                    
                code_df = pd.concat([code_df,tmp_df])
                
            code_df['mean_price'] = code_df['amount']*10/code_df['vol']
            trade_day = code_df.index[0]
            
            
            data_info_df = pro.stock_basic(exchange='', list_status='L', fields='ts_code,industry,list_date')
            data_info_df['trade_date'] = today
            data_info_df['trade_date'] = data_info_df['trade_date'].apply(lambda x:datetime.datetime.strptime(x,"%Y%m%d"))
            data_info_df['list_date'] = data_info_df['list_date'].apply(lambda x:datetime.datetime.strptime(x,"%Y%m%d"))
            data_info_df['PeriodToMar'] = data_info_df['trade_date'] - data_info_df['list_date']
            data_info_df['PeriodToMar'] = data_info_df['PeriodToMar'].apply(lambda x:x.days)
            data_info_df = data_info_df[data_info_df['PeriodToMar'] > 270]
            data_info_df = data_info_df[['ts_code','industry','list_date']]
        
            top_info_df = pd.read_csv(top10_path)
            
            
            totals_df = pro.daily_basic(ts_code='', trade_date=today, fields='ts_code,total_share')
            if totals_df.shape[0] == 0:
                totals_df = pro.daily_basic(ts_code='', trade_date=trade_day, fields='ts_code,total_share')
            else:
                pass
            if totals_df.shape[0] == 0:
                print ('Error')
                return 0
            
            code_df = pd.merge(data_info_df,code_df,how='left',on=['ts_code'])
            code_df = pd.merge(code_df,totals_df,how='left',on=['ts_code'])
            code_df = pd.merge(code_df,top_info_df,how='left',on=['ts_code'])
            
            code_df.dropna(how='any',inplace=True)
            code_df['totals_mv'] = code_df['close']*code_df['total_share']
            code_df['totals_mv'] = code_df['totals_mv']/10000
            code_df['mean_price'] = code_df['amount']*10/code_df['vol']
            code_df['trade_date'] = code_df['trade_date'].apply(lambda x:datetime.datetime.strptime(str(x),"%Y%m%d"))
            #code_df['list_date'] = code_df['list_date'].apply(lambda x:datetime.datetime.strptime(x,"%Y%m%d"))
            code_df['PeriodToMar'] = code_df['trade_date'] - code_df['list_date']
            code_df['PeriodToMar'] = code_df['PeriodToMar'].apply(lambda x:x.days)
            code_df['cq_sign'] = 0
            code_df['ts_code'] = code_df['ts_code'].apply(lambda x:int(x.replace('.SH','').replace('.SZ','')))
            code_df = code_df[['trade_date','ts_code','open','high','close','pre_close','vol','mean_price','amount','pct_chg','turnover_rate','hold_ratio',\
                               'top10_d_r','industry','totals_mv','PeriodToMar','cq_sign']]
            code_df.dropna(how='any',inplace=True)
            print('无交易写文件')
            code_df.to_csv(daily_path,encoding='utf-8',index=False)
            #code_df.to_csv(daily_path,encoding='utf-8',index=False)
            return 1
    except Exception as ex:
        print('异常',ex)
        return 0

cf=configparser.ConfigParser()
ini_path = os.path.dirname(os.path.realpath(sys.argv[0])) + '/test.ini'
print (ini_path)
cf.read(ini_path)
token=cf.get('info','token')
save_path = cf.get('info','path')
level = int(cf.get('info','level'))
save_path = os.path.dirname(os.path.realpath(sys.argv[0])) + save_path
print (token)
print (save_path)
print (level)
token = '92fa5b4defcb65d71defd90b46b240ad77860cc3c0ec0958e492172d'
sig = update_data(token,save_path,level)
if sig == 0:
    print ('Update data fail!')
else:
    print ('Update data success!')
