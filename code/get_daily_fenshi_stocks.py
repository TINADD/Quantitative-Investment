import os
import tushare as ts
import pandas as pd
import datetime
import time
import numpy as np

token = '92fa5b4defcb65d71defd90b46b240ad77860cc3c0ec0958e492172d'
ts.set_token(token)
pro = ts.pro_api()

#给定下载日期，比如要测试19年11月到现在的数据，需要从19年10月开始下载
#获取20200101-20201001之间的股票数据[0101,1001)
start_date_bef = '20201006' #从当前日期开始下载
start_date_rel = '20201101' #实际需要的起始日期
end_date = '20201201' #实际的要获取股票数据的结束日期,获取结果不含该日期

#f:\SmartLab\Quantitative-Investment/stockdata/
top10_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__))) + '/stockData/top10.csv'
saved_path = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))+'/stockdata/dataDownload/'+start_date_rel+'_'+end_date+'/' #当前程序下载的所有文件都存在此目录下
daily_path = saved_path+'DailySingle/' #日线数据存储路径，一只股票一个文件
fenshi_path = saved_path+'Fenshi/'

def mkdir(path):
 
	folder = os.path.exists(path)
 
	if not folder:                   #判断是否存在文件夹如果不存在则创建为文件夹
		os.makedirs(path)            #makedirs 创建文件时如果路径不存在会创建这个路径
		print ("---  new folder...  ---")
		print ("---  OK  ---")
 
	else:
		print ("---  There is this folder!  ---")

#Turn different time format to the datetime[64]
def FormatTime(str_x):
    try:
        return pd.to_datetime(str_x,format="%Y%m%d")
    except ValueError:
        return pd.to_datetime(str_x)
 

mkdir(saved_path)
mkdir(daily_path)
mkdir(fenshi_path)

#只获取上市的公司股票code
#只获取上市的公司股票code
def get_minute_data():
    stock_basic = pro.stock_basic(exchange_id='', is_hs='',list_status='L', fields='ts_code,industry,list_date')

    end_date_rel = (datetime.datetime.strptime(end_date,'%Y%m%d') +  datetime.timedelta(days=1)).strftime('%Y%m%d')
    #获取交易日历
    trade_cal = pro.trade_cal(exchange='', start_date=start_date_rel, end_date=end_date_rel)
    #过滤掉不交易日期
    trade_cal = trade_cal[trade_cal.is_open == 1]
    date_list = list(trade_cal.cal_date)

    stocks_minute = pd.DataFrame() #记录所有股票的分时数据 1min
    for code in stock_basic['ts_code']:
        try:
            code_min = ts.pro_bar(ts_code=code, adj='qfq',start_date=start_date_rel, end_date=end_date_rel, freq='1min')
        except:
            time.sleep(1)
            code_min = ts.pro_bar(ts_code=code, adj='qfq',start_date=start_date_rel, end_date=end_date_rel, freq='1min')
        if(code_min is None):
            print('code_min is None')
            print(code_min)
            continue
        #print(code_min)
        code_min['trade_time'] = pd.to_datetime(code_min['trade_time'])
        code_min['date'] = code_min['trade_time'].apply(lambda x:x.date())
        code_min['time'] = code_min['trade_time'].apply(lambda x:x.time())
        
        code_min.time = code_min.time.astype(str)
        code_min = code_min[code_min.time<='11:00:00']
        code_min = code_min[['trade_time','ts_code','open','close','high','low','date','time']]
        stocks_minute = pd.concat([stocks_minute,code_min])
    stocks_minute['ts_code'] =stocks_minute['ts_code'].apply(lambda x: int(x.replace('.SH', '').replace('.SZ', '')))
    #修改列名
    stocks_minute.rename(columns={'trade_time':'datetime','ts_code':'code'},inplace=True)
    print('写分时数据...')    
    stocks_minute.to_csv(saved_path+'Fenshi'+start_date_rel+'-'+end_date+'.csv')

def get_daily_data():
    stocks_daily = pd.DataFrame() #记录所有股票的日线数据
    stocks_daily_source = pd.DataFrame()

    stock_basic = pro.stock_basic(exchange_id='', is_hs='',list_status='L', fields='ts_code,industry,list_date')
    
    for code in stock_basic['ts_code']:
        print(code)
        try:
            #Index(['trade_date', 'ts_code', 'open', 'high', 'low', 'close', 'pre_close',
            #'change', 'pct_chg', 'vol', 'amount', 'turnover_rate'],dtype='object')
            code_daily = ts.pro_bar(ts_code=code, adj='qfq', start_date=start_date_bef, end_date=end_date,factors=['tor'])
        except:
            time.sleep(0.2) #休眠0.2s
            code_daily = ts.pro_bar(ts_code=code, adj='qfq', start_date=start_date_bef, end_date=end_date,factors=['tor'])
        #增加换手率信息
        try:
            tor_daily_basic = pro.daily_basic(ts_code=code, start_date=start_date_bef, end_date=end_date, fields='ts_code,trade_date,total_share')
        except:
            time.sleep(0.2)
            tor_daily_basic = pro.daily_basic(ts_code=code, start_date=start_date_bef, end_date=end_date, fields='ts_code,trade_date,total_share')
        if(code_daily is None):
            print('code_daily is None')
            print(code_daily)
            continue
        if(tor_daily_basic is None):
            print('tor_daily_basic is None')
            print(tor_daily_basic)
            continue
        #合并code日线数据
        code_daily = pd.merge(code_daily,tor_daily_basic,how='left',on=['trade_date','ts_code'])    
        #print(code_daily.columns)
        #计算平均价格
        code_daily['mean_price'] = (code_daily['amount']/code_daily['vol'])*10

        #计算股票上市日期
        stock_basic['trade_date'] = end_date
        #stock_basic['trade_date'] = stock_basic['trade_date'].apply(lambda x:datetime.datetime.strptime(x,"%Y%m%d"))
        #stock_basic['list_date'] = stock_basic['list_date'].apply(lambda x:datetime.datetime.strptime(str(x),"%Y%m%d"))
        stock_basic.list_date = pd.to_datetime(stock_basic.list_date,format="%Y%m%d")
        stock_basic.trade_date = pd.to_datetime(stock_basic.trade_date,format="%Y%m%d")

        stock_basic['PeriodToMar'] = stock_basic['trade_date'] - stock_basic['list_date']
        stock_basic['PeriodToMar'] = stock_basic['PeriodToMar'].apply(lambda x:x.days)
         
        #截取上市天数>270天的股票 选股策略1
        stock_basic = stock_basic[stock_basic['PeriodToMar'] > 270]
        stock_basic = stock_basic[['ts_code','industry','PeriodToMar','list_date']]
        
        code_daily = pd.merge(code_daily,stock_basic,how='left',on=['ts_code'])

        #读取十大股东数据
        top10_df = pd.read_csv(top10_path)
        code_daily = pd.merge(code_daily,top10_df,how='left',on=['ts_code'])
        
        #得到总市值信息
        code_daily['totals_mv'] = code_daily['close']*code_daily['total_share']#zqy：这个公式哪里来的
        code_daily['totals_mv'] = code_daily['totals_mv']/10000 #万元为单位
        code_daily['totals1'] = code_daily['total_share']*code_daily['pre_close']

        code_daily['trade_date'] = code_daily['trade_date'].apply(lambda x:datetime.datetime.strptime(str(x),"%Y%m%d"))
        code_daily['cq_sign'] = 0
        code_df['ts_code'] = code_daily['ts_code'].apply(lambda x:int(x.replace('.SH','').replace('.SZ','')))
        code_df = code_df[['trade_date','ts_code','open','high','close','pre_close','vol','mean_price','amount','pct_chg','turnover_rate','hold_ratio',\
                               'top10_d_r','industry','totals_mv','PeriodToMar','cq_sign']]
        code_df.dropna(how='any',inplace=True)#存在NAN值时删除该行
        stocks_daily_source = pd.concat([stocks_daily_source,code_df])
        code_daily.dropna(how='any',inplace=True)#存在NAN值时删除该行
        
        #保存前12个交易日涨幅
        for i in range(1,13):
            code_daily['cp'+str(i)] = code_daily['pct_chg'].shift(-i)
        #保存前5个交易日的成交量
        for j in range(1,6):
            code_daily['vol'+str(j)] = code_daily['vol'].shift(-j)

        #确定买入前五天涨幅
        code_daily['cp_sum_five'] = 0
        for j in range(1,6):
            code_daily['cp_sum_five'] = code_daily['cp_sum_five'] + code_daily['cp'+str(j)]
        
        #后两个交易日
        code_daily['day_tomo'] = code_daily['trade_date'].shift(1)
        code_daily['day_tomo'] = code_daily['day_tomo'].apply(lambda x:(str(x).replace('.0','')))
        code_daily['day_tomo'] = code_daily['day_tomo'].apply(lambda x:FormatTime(x))
        code_daily['day_aftertomo'] = code_daily['trade_date'].shift(2)
        code_daily['day_aftertomo'] = code_daily['day_aftertomo'].apply(lambda x:(str(x).replace('.0','')))
        code_daily['day_aftertomo'] = code_daily['day_aftertomo'].apply(lambda x:FormatTime(x))
        
        #选股当天的换手率->前一天的换手率
        code_daily['tr_before'] = code_daily['turnover_rate'].shift(-1)
        
        code_daily['high1'] = code_daily['high'].shift(-1)
        code_daily['high2'] = code_daily['high'].shift(-2)
        code_daily['open1'] = code_daily['open'].shift(-1)
        code_daily['open2'] = code_daily['open'].shift(-2)
        code_daily['close1'] = code_daily['close'].shift(-1)
        code_daily['close2'] = code_daily['close'].shift(-2)
        code_daily['close3'] = code_daily['close'].shift(-3)

        #policy3:（买入前两天的收盘最高价-买入前两天开盘最低价）/买入前两天开盘最低价）
        code_daily['close_highest_2bef'] = code_daily[['close1','close2']].max(axis=1)
        code_daily['open_lowest_2bef'] = code_daily[['open1','open2']].min(axis=1)

        code_daily['policy3'] = (code_daily['close_highest_2bef']-code_daily['open_lowest_2bef'])/code_daily['open_lowest_2bef']*100

        #获取前30天的收盘最高价&收盘最低价
        code_daily['close_highest'] = 0
        code_daily['close_lowest'] = 0
        for i in range(0,code_daily.shape[0]-22,1):
            pre_22day = code_daily.iloc[i+1:i+23]
            #print(pre_22day['close'])
            try:
                code_daily.loc[i,'close_highest'] = max(pre_22day['close'])
            except ValueError:
                code_daily.loc[i,'close_highest'] = np.nan
            try:
                code_daily.loc[i,'close_lowest'] = min(pre_22day['close'])
            except ValueError:
                code_daily.loc[i,'close_lowest'] = np.nan
        code_daily.to_csv(daily_path+str(code)+'.csv',index=False)
        #policy1:收盘价与前30天包括选股当天的最高收盘价差值比例--前22个交易日收盘最高价-当天收盘价/当天收盘价
        code_daily['policy1'] = (code_daily['close_highest'] - code_daily['close1'])/code_daily['close1']

        #policy2:选股当天成交量大于昨日成交量*1
        code_daily['policy2'] = code_daily['vol1']/code_daily['vol2']

        #得出卖出当天是否会开盘涨停 after_sign
        code_daily['high_tomo'] = code_daily['high'].shift(1)
        code_daily['low_tomo'] = code_daily['low'].shift(1)
        code_daily['after_sign'] = (code_daily['high_tomo'] == code_daily['low_tomo'])
        code_daily['after_sign'] = code_daily['after_sign'].astype(int)

        code_daily['h_l_diff'] = (code_daily['close_highest'] - code_daily['close_lowest'])/code_daily['close_lowest']

        #code_daily.drop(['Unnamed: 0'],axis=1,inplace=True)

        stocks_daily = pd.concat([stocks_daily,code_daily]) #股票数据拼接
    stocks_daily['ts_code'] =stocks_daily['ts_code'].apply(lambda x: int(x.replace('.SH', '').replace('.SZ', '')))
    #修改列名
    stocks_daily.rename(columns={'trade_date':'datetime','ts_code':'code','mean_price':'mean_value4_before','close1':'settlement',\
                          'hold_ratio':'top10sh'},inplace=True)
    stocks_daily.rename(columns={'close_highest':'30_close_highest','cp_sum_five':'cp_sum'},inplace=True)
    #删除多余日期的股票
    stocks_daily_final = stocks_daily_final[pd.to_datetime(stocks_daily_final['datetime'],format="%Y/%m/%d")>= pd.to_datetime(start_date_rel,format="%Y/%m/%d")]
    stocks_daily_final['mean_value2_hl_before'] = stocks_daily_final['mean_value4_before']
    stocks_daily_final['mean_value_oc_before'] = stocks_daily_final['mean_value4_before']
    stocks_daily_final = stocks_daily_final[['datetime','code','totals1','policy3','open','high','mean_value2_hl_before','policy1','policy2','tr_before',\
                     'settlement','30_close_highest','mean_value4_before','low','top10sh','after_sign','day_tomo',\
                     'day_aftertomo','cp_sum','cq_sign','mean_value_oc_before','close','h_l_diff']]
    stocks_daily_source['h_l_diff'] = stocks_daily_final['h_l_diff']
    print('写日线数据...')
    stocks_daily_source.to_csv(saved_path+'new_daily'+start_date_rel+'-'+end_date+'_source.csv',index=False)
    stocks_daily_final.to_csv(saved_path+'new_daily'+start_date_rel+'-'+end_date+'.csv',index=False)

if __name__ == '__main__':
    #get_daily_data()
    get_minute_data()