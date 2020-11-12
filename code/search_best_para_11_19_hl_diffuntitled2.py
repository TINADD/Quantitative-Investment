# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 16:32:22 2019

改动：增加前22个交易日的涨幅信息作为筛选
测！！最优！！参数组合

-----------------------------
在ver9上的基础改动之处：
对不正常的均价进行了处理
有三种选法
1-用最高最低的平均值
2-用开盘收盘的平均值
3-用这四个值得平均值

然后由于成交量 我们得数据都是原始数据 没有经过复权处理得
所以现在 最简单的方式：除权的股票当天不进行选择范围
-----------------------------
在现今效果最好的版本上面改进--精简版


这个主要就是分析数据--把固定属性都放松
之前观察到换手率还是有影响的 所以保存换手率
与最高价差也关系到买入价格设定 所以保存

现在只考虑静态的
但是增加一些筛选条件
1.前五天的涨幅 不能太高 也不能太少  3-20
2.单价 大于5小于50

现在卖出策略变动更大
变成 卖出价格跟买入价有关系而且跟卖出当天开盘价有关系
OP>=BP: 开盘价>=买入价
    LB = max{BP, OP+a*BP}
    UB = min{BP+c*BP,OP+b*BP}
OP<BP: 开盘价<买入价
    LB = OP+a*BP
    UB = max{BP,OP+b*BP}
    
分情况讨论：
初始参数设定 之后还要调参
总市值 >= 100时：
a = -0.5%  b=4%
总市值 < 100时：
a = -0.4%  b=5%
当买入价格<=30时：
d_price = 1.05
a = a*1.05 b=b*1.05

买入策略变简单：
不买的情况 --
1.当天价格一直高于昨日收盘 的 1.01
2.当天的价格一直低于 昨日收盘的 0.98

买入的情况：
3.当天开盘 处于 昨日收盘的 0.98 到  昨日收盘 的 1.01 之间
4.当天开盘高于 昨日收盘 的 1.01 但是后来降低到 昨日收盘 的 1.01
5.当天开盘低于 昨日收盘的 0.98 但后来涨到 昨日收盘的 0.98

由于原来的买入策略更加好
所以在原来策略上改进

新引入减少回撤的策略
#1.在股票数<10时 不进行股票购买操作
#2.每支股票的最大购买金额为5万元
#这些值都设为参数
#
#先不考虑金额  将股票数下限设为5
#然后结合时间来考虑
#如果当天的利润 <-0.01
#则第二天不进行买入
#以此类推
（以上暂未考虑 只考虑了预警机制）

加入动态变化的预警机制
如果 当天股票个数<10且 利润<-0.01/-0.005（设为参数） 进入预警期
但是如果遇到大于10的股票数的日期 则跳出预警期
入股处在预警期的时间比较长，则最小股票数（10）变大

预警期：就是股票数小于（最小股票数）10时 直接不进行购买

引进高级预警机制：(随时可以进入 不管是不是在警戒状态)
连续5天的利润之和 低于-10%（若没有买入 我们便当这天利润为-3%） 我们便进入高级预警状态
只模拟买入 不真正的操作 到真正的盈利
再转到预警模式


@author: PC
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
import time
import os
from random import sample

start_date = '20200101'
end_date = '20201001'

#Q
top10sh_list = [i for i in range(20,80,10)] #十大股东占比
tr_list = [j/10.0 for j in range(20,41)] #换手率
policy1_list = [i/100.0 for i in range(1,7)] #('30_close_highest'-'close1')/'close1' 收盘价与前30天（其实只有22天交易日）包括选股当天的最高收盘价差值比例
cp_down_list = [i for i in range(2,6)] #前五天涨幅下限-changepercent
policy2_list = [j/10 for j in range(17,21)] # code_df['vol1']/code_df['vol2'] 昨日成交量/前日成交量 即对应策略中“选股当天成交量大于昨日成交量*1”
cp_up_list = [j for j in range(18,23)] #前五天涨幅上限-changepercent -对应策略中“买入前五天涨幅大于4小于8”
totals1_down_list = [i for i in range(90,130)] #总市值下限
price_down_list = [i for i in range(3,8)] #昨日收盘价格下限
price_up_list = [i for i in range(40,51)] #昨日收盘价格上限
#totals1_up_list = [100,110,95,98,97,96,120]
totals1_up_list = [1000,1100,950,980,970,960,1200] #总市值上限
policy3_list = [i/10.0 for i in range(160,200)] #买入前两天到达的涨幅（（收盘最高close_highest-开盘最低价open_lowest）/开盘最低价open_lowest）

#
##卖出的条件的参数
##100以上的
#a_up100_list = [-i/1000 for i in range(1,6)]
#b_up100_list = [j/100.0 for j in range(3,8)]
##100以下的
#a_down100 = -0.004
#b_down100 = 0.05
##固有标准
#c_list = [i/1000.0 for i in range(70,86)]
#
##单价小于30时的变换参数
#d_price = 1.05
#
##决定买入价格的参数
#qu_num_list = [i/100.0 for i in range(95,100)]
#mulh_num_list = [i/100.0 for i in range(95,100)]
#settle_num_list = [i/100.0 for i in range(95,105)]
#sell_minute_list = [615,600,630,645,660]

#top10sh_list = [30,50,70]
#tr_list = [3.7,2,4]
#policy1_list = [0.04,0.06,0.02]
#cp_down_list = [3,4,5]
#policy2_list = [1.2,1.5,2]
#cp_up_list = [20,22,19]
#totals1_down_list = [104,100,110]
#price_down_list = [7,5,3]
#price_up_list = [40,45,50]
#totals1_up_list = [1000,1100,1200]
#policy3_list = [20,22,18]

#卖出的条件的参数
#100以上的
a_up1001_list = [-i/1000 for i in range(1,2)]   #卖出当天低开较多
a_up1002_list = [-i/1000 for i in range(1,6)]    #卖出当天低开较少
b_up100_list = [j/100.0 for j in range(3,8)]
#100以下的
a_down100 = -0.004
b_down100 = 0.05
#固有标准
c_list = [i/1000.0 for i in range(80,86)]

#单价小于30时的变换参数
d_price = 1.05

#决定买入价格的参数
qu_num_list = [i/100.0 for i in range(96,100)]
mulh_num_list = [i/100.0 for i in range(96,100)]
settle_num_list = [i/100.0 for i in range(100,105)]
sell_minute_list = [615,600,630,645,660]

#股票支数限制参数
min_stock_num_list = [i for i in range(5,16)]
#股票金额
max_stock_pay = 20

#固定无关参数
a_down100 = -0.004
b_down100 = 0.05
para1 = 0
para2 = 0

#记录错误的地方
date_format_err = []
sell_miss_list = []
code_miss_list = []
bug_test = []
print('初始化全局变量end')

#将str类型变为datetime类型
def return_datetime(string):
    try:
        return datetime.datetime.strptime(string, "%Y-%m-%d")
    except ValueError:
        return datetime.datetime.strptime(string, "%Y/%m/%d")
    
def return_datetime_final(string):
    try:
        return datetime.datetime.strptime(string, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return datetime.datetime.strptime(string, "%Y-%m-%d")

#将str类型变为 datetime类型 - - 针对分时的数据
def to_datime(ex_string):
    try:
        return (datetime.datetime.strptime(ex_string, "%Y-%m-%d %H:%M:%S"))
    except ValueError:
        try:
            return (datetime.datetime.strptime(ex_string, "%Y/%m/%d %H:%M"))
        except ValueError:
            date_format_err.append(ex_string)
            return np.nan    
        
        
def MarketToTime(st):
    try:
        return datetime.datetime.strptime(str(st), "%Y%m%d")
    except ValueError:
        return np.nan
    


def mkdir(path):
 
	folder = os.path.exists(path)
 
	if not folder:                   #判断是否存在文件夹如果不存在则创建为文件夹
		os.makedirs(path)            #makedirs 创建文件时如果路径不存在会创建这个路径
		print ("---  new folder...  ---")
		print ("---  OK  ---")
 
	else:
		print ("---  There is this folder!  ---")
        
def get_not(tmp_list):
    return_list = []
    for i in tmp_list:
        d = not(i)
        return_list.append(d)
    return return_list

def leave2(tmp_list):
    return_list = []
    for a in tmp_list:
        if np.isnan(a): #a不是一个数字
            return_list.append(a)
        else:
            b = np.around(float(a), decimals=2) #四舍五入保留小数后两位
            return_list.append(b)
    return return_list

def min_max1(series):
    min_v = np.min(series)
    max_v = np.max(series)
    series = series.apply(lambda x:(x-min_v)/(max_v-min_v))
    return series



#buy_matrix ----'code','buy','after_sign','day_tomo','day_aftertomo','totals1'  注意后两者的日期格式！！
#after_sign?
# 决定卖出策略的上下界 
def decision_sp_ub(totals,bp,op,cp,a_up1001,a_up1002,b_up100,c):
    '''
    totals:总市值
    bp:买入价格;op:开盘价;cp:前五天涨幅
    a_up1001:卖出价格参数，总市值在100以上
    a_up1002:
    b_up100
    c

    '''
    if totals<totals:
        if op>=bp: #开盘价>=买入价
            lb = max(bp, (op+a_down100*bp))
            ub = min((cp+c*cp),(bp+c*bp),(op+b_down100*bp))
        else: #开盘价<买入价
            lb = op+a_down100*bp
            ub = max(bp,(op+b_down100*bp))
    else:
        if op>=bp:#开盘价>=买入价
            lb = max(bp, (op+a_up1002*bp))
            ub = min((cp+c*cp),(bp+c*bp),(op+b_up100*bp))
        elif op<= bp*0.98: #开盘价<=买入价*0.98
            lb = op+a_up1001*bp
            ub = max(bp,(op+b_up100*bp))
        else: 
            lb = op+a_up1002*bp
            ub = max(bp,(op+b_up100*bp))
    return lb,ub
#def decision_sp_ub(totals,bp,op,cp,a_up100,b_up100,c):
#    if totals<totals:
#        if op>=bp:
#            lb = max(bp, (op+a_down100*bp))
#            ub = min((cp+c*cp),(bp+c*bp),(op+b_down100*bp))
#        else:
#            lb = op+a_down100*bp
#            ub = max(bp,(op+b_down100*bp))
#    else:
#        if op>=bp:
#            lb = max(bp, (op+a_up100*bp))
#            ub = min((cp+c*cp),(bp+c*bp),(op+b_up100*bp))
#        else:
#            lb = op+a_up100*bp
#            ub = max(bp,(op+b_up100*bp))
#    return lb,ub
        
            
'''
Func:sell_result_update_ver2 -- to determine the sell price
Input:buy_matrix,day,day_after,m,a_up100,b_up100,sell_minutes
Format:buy_matrix -- 'code','buy','after_sign','day_tomo','day_aftertomo','totals1','settlement'
        fenshi_matrix -- 'datetime','code','open','close','high','low','date','time'
Output:df_sell -- sell dataframe
Format:'code','sell','SellPolicy','sell_lb','sell_ub','max_p','min_p','f_p','open_p'
'''
def sell_result_update_ver2(buy_matrix,day,day_after,m,a_up1001,a_up1002,b_up100,sell_minutes,c): #买入矩阵 该天 后一天 买入个数
    print('确定卖出价格','\n')
    #得到是卖出该天的分时数据
    print('买入当天',day,'\n')
    print ('卖出当天',day_after,'\n')
    fenshi = fenshi_df[fenshi_df.date==day_after]
    #print ('after  choose day:')
    #print (fenshi.shape)
    result_list = np.full([m,9],np.nan)
        
    for i in range(m):
        codeid  = str(int(buy_matrix[i,0])).zfill(6)
        buy = buy_matrix[i,1]
        sign = buy_matrix[i,2]
        totals = buy_matrix[i,5]
        close = buy_matrix[i,6]
        #得到该code的分时数据 不过可能为None值
        '''下面只是得到 open_p的值 就是op的值 以及对应的fenshi_matrix  分为卖出当天有无涨停的情况'''
        if sign==0: #没有卖出当天开盘涨停的情况
            sell_tmp = fenshi[fenshi['code'] == codeid]
            #print (sell_tmp.head())
            date_slice = day_after
            date_slice1 = date_slice + datetime.timedelta(minutes=sell_minutes)
            fenshi_tmp = sell_tmp[sell_tmp['datetime']>date_slice]
            fenshi_tmp = fenshi_tmp[fenshi_tmp['datetime']<=date_slice1]
            #print (fenshi_tmp.head())
            fenshi_matrix = fenshi_tmp.values
            try:
                #可能分时矩阵没有数据 raise exception
                open_p = fenshi_matrix[-1,2]
            #这种错误的股票中间情况 就是 该出现了停牌 导致卖出当天不是 一般的下一个交易日
            #解决办法是得到该股的下一个交易日
            #new#停牌 获取 day_tomo读取 day_tomo的分时数据
            except IndexError:
                print ("May data loss or tingpai!")
                try:
                    fenshi1 = fenshi_df[fenshi_df.date==buy_matrix[i,3]]
                    print ('AFTER CHOOSING DAY:')
                    print (fenshi1.shape)
                    sell_tmp = fenshi1[fenshi1['code'] == codeid]
                    #此时的day_tomo应该已经是datetime形式？
                    date_slice = buy_matrix[i,3]
                except:
                    #fenshi缺少数据
                    code_miss_list.append([date_slice,codeid])
                    #result_list[i] = [np.nan,np.nan]
                    print (fenshi1)
                    time.sleep(3)
                    continue
                    
                date_slice1 = date_slice + datetime.timedelta(minutes=sell_minutes)
                fenshi_tmp = sell_tmp[sell_tmp['datetime']>date_slice]
                fenshi_tmp = fenshi_tmp[fenshi_tmp['datetime']<=date_slice1]
                fenshi_matrix = fenshi_tmp.values
                #可能 在final_matrix里面有数据 但是分时数据缺失
                try:
                    open_p = fenshi_matrix[-1,2]
                except IndexError:
                    sell_miss_list.append([date_slice,codeid])
                    continue
           
        #sign表示卖出当天开盘涨停 所以再后面一天卖出
        else:
            try:
                fenshi_olu = fenshi_df[fenshi_df.date==buy_matrix[i,4]]
                sell_tmp = fenshi_olu[fenshi_olu['code'] == codeid]
                #此时的day_tomo应该已经是datetime形式
                date_slice = buy_matrix[i,4]
            except:
                #真的没有数据了
                code_miss_list.append([date_slice,codeid])
                #result_list[i] = [np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan]
                print (fenshi_olu)
                time.sleep(3)
                continue
                
            date_slice1 = date_slice + datetime.timedelta(minutes=sell_minutes)
            fenshi_tmp = sell_tmp[sell_tmp['datetime']>date_slice]
            fenshi_tmp = fenshi_tmp[fenshi_tmp['datetime']<=date_slice1]
            fenshi_matrix = fenshi_tmp.values
            #可能 在final_matrix里面有数据 但是分时数据缺失
            try:
                open_p = fenshi_matrix[-1,2]
            except IndexError:
                sell_miss_list.append([date_slice,codeid])
                continue
            
            
        lb,ub = decision_sp_ub(totals,buy,open_p,close,a_up1001,a_up1002,b_up100,c)
        max_p = max(fenshi_matrix[:,4])
        min_p = min(fenshi_matrix[:,5])
        f_p = fenshi_matrix[0,3]
        

        
        tmp_list = []
        #改这一块
        m = fenshi_matrix.shape[0]
        #开盘大于上界
        if(open_p >= ub):
            tmp_list = [codeid, open_p, 4, lb, ub, max_p, min_p, f_p, open_p]
        #未达到上界 但是达到下界
        elif ((max_p < ub) & (min_p <= lb)):
            tmp_list = [codeid, lb, 1, lb, ub, max_p, min_p, f_p, open_p]
        #达到上界 未达到下界
        elif ((max_p >= ub) & (min_p > lb)):
            tmp_list = [codeid, ub, 2, lb, ub, max_p, min_p, f_p, open_p]
        #未达到上界 也未达到下界 中间波动 最后卖出
        elif ((max_p < ub) & (min_p > lb)):
            tmp_list = [codeid, f_p, 3, lb, ub, max_p, min_p, f_p, open_p]
        #既达到了上界 也达到了下界
        else:
            #对于每分钟 先判断是否达到了 上界
            #需要先判断开盘是否低于下界或者高于上界
            for j in range(1,m+1): 
                if (fenshi_matrix[-1*j,2]) >= ub:
                    tmp_list = [codeid, ub, 2, lb, ub, max_p, min_p, f_p, open_p]
                    break
                elif ((fenshi_matrix[-1*j,2]) <= lb):
                    tmp_list = [codeid, lb, 1, lb, ub, max_p, min_p, f_p, open_p]
                    break
                elif ((fenshi_matrix[-1*j,5]) <= lb):
                    tmp_list = [codeid, lb, 1, lb, ub, max_p, min_p, f_p, open_p]
                    break
                elif (fenshi_matrix[-1*j,4]) >= ub:
                    tmp_list = [codeid, ub, 2, lb, ub, max_p, min_p, f_p, open_p]
                    break
                        
        #print (tmp_list)
        try:
            result_list[i] = tmp_list
        except ValueError:
            t_list = [codeid, ub, 2, lb, ub, max_p, min_p, f_p, open_p]
            bug_test.append(t_list)
            continue
        
    df_sell = pd.DataFrame(result_list,columns=['code','sell','SellPolicy','sell_lb','sell_ub','max_p','min_p','f_p','open_p'])
    return df_sell


#最新的买入策略  去掉 创新高的情况  以及改进策略4/5时的情况 均价-stock[12]  30天最高-stock[11] 昨日收盘-stock[10]
# 如果买入股票当天高开或者平开 则以1%为界限 
# 如果买入股票当天 低开 则尝试以 -1%/-2%/0.97H (现在还是0.97H)来区分情况
# 在这个界限之下 则 必须达到 max{昨日收盘，昨日均价再买入}
# 在这个界限之上 则 达到 min{昨日收盘，昨日均价再买入} 或者开盘低于此最小值直接买入
    
'''
function:bp_decision_ver3  ---  To decide the buy price and policy.
Input: choose_matrix -- Chosen Stocks Matrix   
Format:'datetime','code','totals1','policy3','open','high','mean_value4_before','policy1','policy2','tr_before',\
                     'settlement','30_close_highest','mean_value2_hl_before','low','top10sh','after_sign','day_tomo',\
                     'day_aftertomo','cp_sum','cq_sign','mean_value_oc_before'
                     
['datetime','code','totals1','policy3','open','high','mean_value4_before','policy1','policy2','tr_before',\
                     'settlement','30_close_highest','mean_value2_hl_before','low','top10sh','after_sign','day_tomo',\
                     'day_aftertomo','cp_sum','cq_sign','mean_value_oc_before','close']

    lb_p 
Output: buy_final_list 
Format: buy_price buy_policy policy4_std(stock[11]*0.97) policy_4_value(min(stock[12],stock[10])) 
                policy_5_value(max(stock[12],stock[10],stock[11]*0.99))
'''
def bp_decision_ver3(choose_matrix1,lb_p,ub_p,para_c):
    '''
    choose_matrix1:已经选好的股票
    lb_p：可调节参数，低开情况
    ub_p：可调节参数，高开情况
    para_c：可调节参数
    '''
    print('开始选择要买入的股票')
    final_list = []
    buy_list = [np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan]
    b_start = time.perf_counter()
    print('遍历已选的每一只股票')
    for stock in choose_matrix1:
        #低开的界限
        '''
        若开盘价open低开，市价≥ lb_p*30天最高价]-policy4_std，等到市价=min{昨日均价,昨日收盘}时或30天最高价，执行买入
        若是开盘open低于min{昨日均价,昨日收盘}，直接买入
        ⑤低开，市价＜lb_p*30天最高价，等到市价达到max{昨日均价，昨日收盘，para_c*30天最高价}时，执行买入
        '''
        #print (stock)
        try:
            #stock[11]:30_close_highest 前30天（即前22个交易日）收盘最高价
            policy4_std = stock[11]*lb_p
        except TypeError:
            print (stock[11])
            time.sleep(60)
        #stock[12]:昨日均价；stock[10]:昨日收盘价    
        policy_4_value = min(stock[12],stock[10])
        policy_5_value = max(stock[12],stock[10],stock[11]*para_c)
        
        buy_list[2] = policy4_std
        buy_list[3] = policy_4_value
        buy_list[4] = policy_5_value
        #开盘 open stock[4]
        buy_list[5] = stock[4]
        #最低 low stock[13]
        buy_list[6] = stock[13]
        #最高 high stock[5]
        buy_list[7] = stock[5]
        #高开 
        #开盘价高于昨日收盘
        if stock[4]>stock[10]:
            #开盘小于收盘价*ub_p 直接开盘买入 策略1
            if(stock[4]/stock[10]<=ub_p):
                buy_list[0] = stock[4] #开盘价买入
                buy_list[1] = 1
            #开盘大于收盘价*ub_p 等跌到最低价<=收盘价*ub_p买入 策略1
            else:
                if(stock[13]/stock[10]<=ub_p):
                    buy_list[0] = stock[10]*ub_p #昨日收盘*ub_p
                    buy_list[1] = 1
                else:
                    buy_list[1] = 6 #?
                
        #平开 的情况      直接开盘价买入  
        elif stock[4]==stock[10]: #今日开盘等于昨日收盘价
            buy_list[0] = stock[4]
            buy_list[1] = 3
        
        #低开的情况 今日开盘小于昨日收盘
        else:
            #若开盘 >前30天 包括当天的最高收盘价（30_close_highest）*lb_p 
            #等市价达到 min{昨日收盘，昨日均价}再买入或者开盘低于此最小值直接买入
            if(stock[4]>=policy4_std): #policy4_std = stock[11]*lb_p
                #开盘小于min{昨日收盘，昨日均价} 直接买入
                if(stock[4]/policy_4_value<=1): #policy_4_value = min(stock[12],stock[10])
                    buy_list[0] = stock[4]
                    buy_list[1] = 4
                    
                #开盘不小于 min{昨日收盘，昨日均价} 但是最低达到过 min{昨日收盘，昨日均价} 以min{昨日收盘，昨日均价}买入
                elif(stock[13]/policy_4_value<=1):
                    buy_list[0] = policy_4_value
                    buy_list[1] = 4
                    
                #开盘不小于min{昨日收盘，昨日均价}，最低价也未达到min{昨日收盘，昨日均价}
                else:
                    #如果都达不到 则不买入 策略8
                    buy_list[1] = 8
            #若开盘 < 前30天包括当天的最高收盘价（30_close_highest）*lb_p 
            # 等市价达到max{昨日收盘，昨日均价}买入 此时开盘都小于昨日收盘了 肯定小于max{昨日收盘，昨日均价}
            #所以只需要看 能不能达到 max{昨日收盘，昨日均价} 能就买 不能就不买入
            else: #最高价high >=  max(昨日均价,昨日收盘,stock[11]*para_c)
                if(stock[5]/policy_5_value>=1): #policy_5_value = max(stock[12],stock[10],stock[11]*para_c)
                    buy_list[0] = policy_5_value
                    buy_list[1] = 5
                else:
                    buy_list[1] = 7
        final_list.append(buy_list)
        buy_list = [np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan]
    b_end = time.perf_counter()
    print('买入股票结束，返回要买入的股票')
    print('Decide the buy price of stocks:')
    print (str(b_end-b_start))
    return final_list

def get_profit_update(data_path,sp,limit,dataset):
    data = dataset[['code','buy','sell','st_or_dy','num']]
    #有些静态选入的股票 并没有买入 所以要去除这一部分
    data.buy = data.buy.astype(float)
    data.st_or_dy = data.st_or_dy.astype(int)
    #data是算所有选入的股票 data1是算所有买入的股票
    data1 = data[np.isnan(data['sell']).apply(lambda x:not x)]
    #cost是每股的成本的百分比
    cost = 0.002
    #这里收益指的是收益率，由于相当于用同样的钱去买每只股，故收益率可以简单平均
    data1['profit'] = (data1['sell'] - data1['buy'])/data1['buy'] - cost
    
    result_all = data.groupby(data.index).sum()

    
    result_buy_count = data1.groupby(data1.index).sum()
    result_buy = data1.groupby(data1.index).mean()
    result_buy['NotBuyNum']  = result_all['num'] - result_buy_count['num']
    result_buy['buy_num'] = result_buy_count['num']
    result_buy['all_num'] = result_all['num']
    result_buy['not_buy_rate'] = result_buy['NotBuyNum']/result_buy['all_num']
    result_buy['buy_rate'] = result_buy['buy_num']/result_buy['all_num']
    
    days = result_buy.shape[0]
    pro = np.zeros(days)
    diff = np.zeros(days)
    #iloc通过行号索引；loc通过行标签索引
    pro[0] = 100 + 100*result_buy.iloc[0].loc['buy_rate']*(result_buy.iloc[0].loc['profit'])
    diff[0] = 0
    for i in range(1,days):
        #没有价格限制
        pro[i] = pro[i-1]*result_buy.iloc[i].loc['not_buy_rate'] + pro[i-1]*result_buy.iloc[i].loc['buy_rate']*(result_buy.iloc[i].loc['profit']+1)
        diff[i] = np.abs(pro[i] - pro[i-1])

    result_buy['real_profit'] = pro
    result_buy['diff'] = diff
    
    
    #去掉大盘信息
    #增加判断 结果不好则不产生图
    #if (pro[-1]>=limit) & (result_buy.shape[0]>(d_length//8)):
    if (pro[-1]>=limit):
        data_file = data_path + sp
        mkdir(data_file)
        Data = result_buy[['profit','real_profit','buy_num','all_num','diff']]
        Data = Data.astype(float)
        Data['profit'] = Data['profit']*1000
        Data['diff'] = Data['diff']*10
        #Data['close'] = (Data['close']-3000)/10
        Data.plot(figsize=(16,12))
        plt.grid(True)
        
        plt.savefig(data_file + '/' + 'profit_num_add_index' + '.png')
        #plt.show()
    else:
        data_file = None
        pass
    
    return result_buy,data_file

#最新的那个策略 （高级预警机制带有延长期）
def make_stock_result_with_advanced_num(p,limit,hl_limit):
    '''
    p:参数列表
    limit:股票收益的下界,低于这个值就不生成文件
    hl_limit:
    '''
    #sp = 'ver4-_danger_signal_num_price_0_strick10_profit' + ('-'+str(a_up100)+'-'+str(a_up100)+'-'+str(policy1)+'-'+str(turnover)+'-'+str(min_stock_num))
    policy1,policy2,policy3,turnover,cp_up,cp_down,top10sh,totals1,totals1_up,price_up,price_down = p[0],p[1],p[2],p[3],p[4],p[5],p[6],p[7],p[8],p[9],p[10]
    a_up1001,a_up1002,b_up100,c,lb_p,para_c,ub_p,min_stock_num,sell_minute = p[11],p[12],p[13],p[14],p[15],p[16],p[17],p[18],p[19]
    sp = 'F:/Smart实验室/量化投资/version-limit0-'+start_date +end_date+'-' +str(policy1) +'-' + str(policy2)+'-' + str(policy3)+'-' + str(turnover)+'-' + str(cp_up)+'-' + str(cp_down)+'-' + str(top10sh)\
    +'-' + str(totals1)+'-' + str(totals1_up)+'-' + str(price_up)+'-' + str(price_down)+'-' + str(a_up1001)+'-' + str(a_up1002)+'-' + str(b_up100)\
    +'-' + str(c)+'-' + str(lb_p)+'-' + str(para_c)+'-' + str(ub_p)+'-' + str(min_stock_num)+'-' + str(sell_minute)+'-' + str(hl_limit)
    
    sp = "20200201-20201101/"
    data_file = data_path + sp
    mkdir(data_file)
    f = open("F:/SmartLab/Quantitative-Investment/code/change1.txt","w")
    
    out_log = open("F:/SmartLab/Quantitative-Investment/code/outlog.txt","w")
    out_002741 = open("F:/SmartLab/Quantitative-Investment/code/outlog.txt","w")
    out_601700 = open("F:/SmartLab/Quantitative-Investment/code/outlog.txt","w")

    start_day = 0
    
    #对于每一天的选股
    special_df = pd.DataFrame(columns=['code','day_aftertomo'])
    t1 = time.perf_counter()
    date_length = len(date_list)-1
    final_choose_df = pd.DataFrame()
    final_earn_df = pd.DataFrame()
    final_lose_df = pd.DataFrame()
    '''测试一下 结合时间和数量和金额'''
    j = start_day
    signal = 0#预警信号
    count = 0
    init_min_stock_num = min_stock_num #5
    pro_sum = 0
    #pro_list 记录真实购买以及模拟买入操作的利润
    pro_list = []
    #pro_test 记录每天的利润 即使没买入或者数据缺失
    pro_test = []
    advanced_signal = 0
    high_count = 0
    #顺序遍历日期中的每一天，进行模拟买卖
    while (j<date_length):
        high_count += 1
        '''
        买卖规则：今天买入，昨天选股，明天卖出
        '''
        #买入当天
        day = date_list[j]
        #卖出当天
        day_after = date_list[j+1]
        #买入前一天---选股当天
        day_before = date_list[j-1]
        if j==0:
            day_before = day 
#        #加入大盘信息判断
#        judge = list(index_df[index_df['trade_date']==day]['indexUse1'])[0]
#        if not judge:
#            j+=1
#            continue
        print(day,'\n')
        #just for test
        t1 = time.perf_counter()
        #对于每一天
        '''
        final_matrix格式 dataframe格式
        'datetime', 'code', 'totals1', 'policy3', 'open', 'high',
       'mean_value4_before', 'policy1', 'policy2', 'tr_before', 'settlement',
       '30_close_highest', 'mean_value2_hl_before', 'low', 'top10sh',
       'after_sign', 'day_tomo', 'day_aftertomo', 'cp_sum', 'cq_sign',
       'mean_value_oc_before','close','lh_diff'
        '''
        #final_matrix 日线数据
        #获取所有日期等于day的股票
        tmp_matrix = final_matrix[final_matrix[:,0]==day]
        out_log.write("买入日期： ")
        out_log.write(str(day.date()))
        out_log.write("\n")

        out_log.write("开始选股......")
        print("开始选股......")
        #静态动态 共同条件 直接把涨幅信息放在这里  总市值大于30小于300
        flag_2512 = True
        flag_601700 = True
        flag_300480 = True
        flag_300493 = True
        flag_603626 = True
        if( '002512' not in  tmp_matrix[:,1]):
            out_log.write('日线数据里没有002512这只股票\n')
            flag_2512  = False
        if('601700' not in  tmp_matrix[:,1]):
            out_log.write('日线数据里没有601700这只股票\n')
            flag_601700 = False
        if( '300480' not in  tmp_matrix[:,1]):
            out_log.write('日线数据里没有300480这只股票\n')
            flag_300480  = False
        if( '300493' not in  tmp_matrix[:,1]):
            out_log.write('日线数据里没有300493这只股票\n')
            flag_300493  = False
        if( '603626' not in  tmp_matrix[:,1]):
            out_log.write('日线数据里没有603626这只股票\n')
            flag_603626  = False
        
        #选取股票总市值小于totals1_up 300
        choose_matrix = tmp_matrix[tmp_matrix[:,2] < totals1_up]
        if('002512' not in  choose_matrix[:,1] and flag_2512 ):
            out_log.write('股票002512总市值>= '+str(totals1_up)+'\n')
            flag_2512  = False
        if('601700' not in  choose_matrix[:,1] and flag_601700):
            out_log.write('股票601700总市值>= '+str(totals1_up)+'\n')
            flag_601700 = False
        if( '300480' not in  tmp_matrix[:,1] and flag_300480):
            out_log.write('股票300480总市值>= '+str(totals1_up)+'\n')
            flag_300480  = False
        if( '300493' not in  tmp_matrix[:,1] and flag_300493):
            out_log.write('股票300493总市值>= '+str(totals1_up)+'\n')
            flag_300493  = False
        if( '603626' not in  tmp_matrix[:,1] and flag_603626):
            out_log.write('股票603626总市值>= '+str(totals1_up)+'\n')
            flag_603626  = False
        
        #选取股票总市值大于totals1 30
        choose_matrix = choose_matrix[choose_matrix[:,2] > totals1]
        if('002512' not in  choose_matrix[:,1] and flag_2512 ):
            out_log.write('股票002512总市值<= '+str(totals1)+'\n')
            flag_2512  = False
        if('601700' not in  choose_matrix[:,1] and flag_601700):
            out_log.write('股票601700总市值<= '+str(totals1)+'\n')
            flag_601700 = False
        if( '300480' not in  tmp_matrix[:,1] and flag_300480):
            out_log.write('日线数据里没有300480这只股票\n')
            flag_300480  = False
        if( '300493' not in  tmp_matrix[:,1] and flag_300493):
            out_log.write('日线数据里没有300493这只股票\n')
            flag_300493  = False
        if( '603626' not in  tmp_matrix[:,1] and flag_603626):
            out_log.write('日线数据里没有603626这只股票\n')
            flag_603626  = False
        #根据policy3选取股票 买入前两天到达的涨幅 最高收盘-最低开盘/最低开盘
        choose_matrix = choose_matrix[choose_matrix[:,3] < policy3]
        if('002512' not in  choose_matrix[:,1] and flag_2512 ):
            out_log.write('股票002512 policy3 >= '+str(policy3)+'\n')
            flag_2512  = False
        if('601700' not in  choose_matrix[:,1] and flag_601700):
            out_log.write('股票601700 policy3 >= '+str(policy3)+'\n')
            flag_601700 = False
        if( '300480' not in  tmp_matrix[:,1] and flag_300480):
            out_log.write('股票300480 policy3 >= '+str(policy3)+'\n')
            flag_300480  = False
        if( '300493' not in  tmp_matrix[:,1] and flag_300493):
            out_log.write('股票300493 policy3 >= '+str(policy3)+'\n')
            flag_300493  = False
        if( '603626' not in  tmp_matrix[:,1] and flag_603626):
            out_log.write('股票603262 policy3 >= '+str(policy3)+'\n')
            flag_603626  = False
        #新增不选取除权的股票 
        choose_matrix = choose_matrix[choose_matrix[:,19] != 1]
        if('002512' not in  choose_matrix[:,1] and flag_2512 ):
            out_log.write('股票002512 已除权\n')
            flag_2512  = False
        if('601700' not in  choose_matrix[:,1] and flag_601700):
            out_log.write('股票601700已除权\n')
            flag_601700 = False
        if( '300480' not in  tmp_matrix[:,1] and flag_300480):
            out_log.write('股票300480 已除权\n')
            flag_300480  = False
        if( '300493' not in  tmp_matrix[:,1] and flag_300493):
            out_log.write('股票300493 已除权\n')
            flag_300493  = False
        if( '603626' not in  tmp_matrix[:,1] and flag_603626):
            out_log.write('股票603626 已除权\n')
            flag_603626  = False
        #新增对前五天的涨幅的约束
        choose_matrix = choose_matrix[choose_matrix[:,18] < cp_up]
        if('002512' not in  choose_matrix[:,1] and flag_2512 ):
            out_log.write('股票002512 cp_up >= '+str(cp_up)+'\n')
            flag_2512  = False
        if('601700' not in  choose_matrix[:,1] and flag_601700):
            out_log.write('股票601700 cp_up >= '+str(cp_up)+'\n')
            flag_601700 = False
        if( '300480' not in  tmp_matrix[:,1] and flag_300480):
            out_log.write('股票300480 cp_up >= '+str(cp_up)+'\n')
            flag_300480  = False
        if( '300493' not in  tmp_matrix[:,1] and flag_300493):
            out_log.write('股票300493 cp_up >= '+str(cp_up)+'\n')
            flag_300493  = False
        if( '603626' not in  tmp_matrix[:,1] and flag_603626):
            out_log.write('股票603626 cp_up >= '+str(cp_up)+'\n')
            flag_603626  = False
        
        choose_matrix = choose_matrix[choose_matrix[:,18] > cp_down]
        if('002512' not in  choose_matrix[:,1] and flag_2512 ):
            out_log.write('股票002512 cp_down <= '+str(cp_down)+'\n')
            flag_2512  = False
        if('601700' not in  choose_matrix[:,1] and flag_601700):
            out_log.write('股票601700 cp_down <= '+str(cp_down)+'\n')
            flag_601700 = False
        if( '300480' not in  tmp_matrix[:,1] and flag_300480):
            out_log.write('股票300480 cp_down <= '+str(cp_down)+'\n')
            flag_300480  = False
        if( '300493' not in  tmp_matrix[:,1] and flag_300493):
            out_log.write('股票300493 cp_down <= '+str(cp_down)+'\n')
            flag_300493  = False
        if( '603626' not in  tmp_matrix[:,1] and flag_603626):
            out_log.write('股票603626 cp_down <= '+str(cp_down)+'\n')
            flag_603626  = False
        
        #静态选股规则
        choose_matrix1 = choose_matrix[choose_matrix[:,7] < policy1*(1+para2)] 
        if('002512' not in  choose_matrix1[:,1] and flag_2512 ):
            out_log.write('股票002512 policy1 >= '+str(policy1*(1+para2))+'\n')
            flag_2512  = False
        if('601700' not in  choose_matrix1[:,1] and flag_601700):
            out_log.write('股票601700 policy1 >= '+str(policy1*(1+para2))+'\n')
            flag_601700 = False
        if( '300480' not in  tmp_matrix[:,1] and flag_300480 ):
            out_log.write('股票300480 policy1 >= '+str(policy1*(1+para2))+'\n')
            flag_300480  = False
        if( '300493' not in  tmp_matrix[:,1] and flag_300493):
            out_log.write('股票300493 policy1 >= '+str(policy1*(1+para2))+'\n')
            flag_300493  = False
        if( '603626' not in  tmp_matrix[:,1] and flag_603626):
            out_log.write('股票603626 policy1 >= '+str(policy1*(1+para2))+'\n')
            flag_603626  = False
        
        choose_matrix1 = choose_matrix1[choose_matrix1[:,8] > policy2]
        if('002512' not in  choose_matrix1[:,1] and flag_2512 ):
            out_log.write('股票002512 policy2 <= '+str(policy2)+'\n')
            flag_2512  = False
        if('601700' not in  choose_matrix1[:,1] and flag_601700):
            out_log.write('股票601700 policy2 <= '+str(policy2)+'\n')
            flag_601700 = False
        if( '300480' not in  tmp_matrix[:,1] and flag_300480):
            out_log.write('股票300480 policy2 <= '+str(policy2)+'\n')
            flag_300480  = False
        if( '300493' not in  tmp_matrix[:,1] and flag_300493):
            out_log.write('股票300493 policy2 <= '+str(policy2)+'\n')
            flag_300493  = False
        if( '603626' not in  tmp_matrix[:,1] and flag_603626):
            out_log.write('股票603626 policy2 <= '+str(policy2)+'\n')
            flag_603626  = False
        
        choose_matrix1 = choose_matrix1[choose_matrix1[:,9] > turnover*(1-para2)]
        if('002512' not in  choose_matrix1[:,9] and flag_2512 ):
            out_log.write('股票002512 换手率 <= '+str(turnover*(1-para2))+'\n')
            flag_2512  = False
        if('601700' not in  choose_matrix1[:,9] and flag_601700):
            out_log.write('股票601700 换手率 <= '+str(turnover*(1-para2))+'\n')
            flag_601700 = False
        if( '300480' not in  tmp_matrix[:,9] and flag_300480):
            out_log.write('股票300480 换手率 <= '+str(turnover*(1-para2))+'\n')
            flag_300480  = False
        if( '300493' not in  tmp_matrix[:,9] and flag_300493):
            out_log.write('股票300493 换手率 <= '+str(turnover*(1-para2))+'\n')
            flag_300493  = False
        if( '603626' not in  tmp_matrix[:,9] and flag_603626):
            out_log.write('股票603626 换手率 <= '+str(turnover*(1-para2))+'\n')
            flag_603626  = False
        
        choose_matrix1 = choose_matrix1[choose_matrix1[:,14] > top10sh*(1-para1)]
        if('002512' not in  choose_matrix1[:,14] and flag_2512 ):
            out_log.write('股票002512 十大股东占比<= '+str(top10sh*(1-para1)) + '\n')
            flag_2512  = False
        if('601700' not in  choose_matrix1[:,14] and flag_601700):
            out_log.write('股票601700 十大股东占比<= '+str(top10sh*(1-para1)) + '\n')
            flag_601700 = False
        if( '300480' not in  tmp_matrix[:,14] and flag_300480):
            out_log.write('股票300480 十大股东占比<= '+str(top10sh*(1-para1)) + '\n')
            flag_300480  = False
        if( '300493' not in  tmp_matrix[:,14] and flag_300493):
            out_log.write('股票300493 十大股东占比<= '+str(top10sh*(1-para1)) + '\n')
            flag_300493  = False
        if( '603626' not in  tmp_matrix[:,14] and flag_603626):
            out_log.write('股票603626 十大股东占比<= '+str(top10sh*(1-para1)) + '\n')
            flag_603626  = False
        
        #增加价格筛选 即对于股票昨日收盘价格进行筛选
        choose_matrix1 = choose_matrix1[choose_matrix1[:,10] <= price_up]
        if('002512' not in  choose_matrix1[:,10] and flag_2512 ):
            out_log.write('股票002512 price_up >'+str(price_up)+'\n')
            flag_2512  = False
        if('601700' not in  choose_matrix1[:,10] and flag_601700):
            out_log.write('股票601700 price_up >'+str(price_up)+'\n')
            flag_601700 = False
        if( '300480' not in  tmp_matrix[:,10] and flag_300480):
            out_log.write('股票300480 price_up >'+str(price_up)+'\n')
            flag_300480  = False
        if( '300493' not in  tmp_matrix[:,10] and flag_300493):
            out_log.write('股票300493 price_up >'+str(price_up)+'\n')
            flag_300493  = False
        if( '603626' not in  tmp_matrix[:,10] and flag_603626):
            out_log.write('股票603626 price_up >'+str(price_up)+'\n')
            flag_603626  = False
        
        choose_matrix1 = choose_matrix1[choose_matrix1[:,10] >= price_down]
        if('002512' not in  choose_matrix1[:,10] and flag_2512 ):
            out_log.write('股票002512 price_down <'+str(price_down)+'\n')
            flag_2512  = False
        if('601700' not in  choose_matrix1[:,10] and flag_601700):
            out_log.write('股票601700 price_down <'+str(price_down)+'\n')
            flag_601700 = False
        if( '300480' not in  tmp_matrix[:,10] and flag_300480):
            out_log.write('股票300480 price_down <'+str(price_down)+'\n')
            flag_300480  = False
        if( '300493' not in  tmp_matrix[:,10] and flag_300493):
            out_log.write('股票300493 price_down <'+str(price_down)+'\n')
            flag_300493  = False
        if( '603626' not in  tmp_matrix[:,10] and flag_603626):
            out_log.write('股票603626 price_down <'+str(price_down)+'\n')
            flag_603626  = False
        #新增
        #对于前22个交易日涨幅筛选
        #print('股票前22个交易日涨幅要<=',hl_limit,'先不用这个策略')
        #choose_matrix1 = choose_matrix1[choose_matrix1[:,22] <= hl_limit]
        
        t2 = time.perf_counter()
        
        '''决定买入,并且将买入的格式改成之后需要的格式
        datetime code  buy buyPolicy  policy4_std policy4_value policy5_value  
        buy_open buy_low buy_high st_or_dy after_sign day_tomo day_aftertomo  
        totals1 settlement open mean_price_before 30_close_highest close
        '''
        print('决定买入，将买入的格式改成之后需要的格式')
        print('决定买入,choose_matrix1.size',choose_matrix1.size)
        if(choose_matrix1.size == 0):
            if signal == 1:
                count += 1
            #pro_test 记录每天的利润，即使没买入或者数据缺失
            pro_test.append([day,0,advanced_signal,signal,pro_sum,high_count,count,min_stock_num,0,0,0])
            #pro_list记录真实购买以及模拟买入操作的利润
            pro_list.append(0)
            j += 1
            continue
        #buy_list = [np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan,np.nan]
        final_list = bp_decision_ver3(choose_matrix1,lb_p,ub_p,para_c)
        #final_list.columns = 8
        print ('选好的买入股票列表,type(final_list)',final_list,type(final_list))
        #保存股票代码和日期
        st_buy_matrix = choose_matrix1[:,[0,1]]
        print ('st_buy_matrix.columns' ,st_buy_matrix.shape[1])
        st_buy_matrix = np.column_stack((st_buy_matrix,final_list)) #拼接st_buy_matrix,final_list
        print('st_buy_matrix.columns',st_buy_matrix.shape[1])
        m = st_buy_matrix.shape[0]
        print("m=",m)
        sd_list = np.zeros((m), dtype=np.int)
        st_buy_matrix = np.column_stack((st_buy_matrix,sd_list))
        print('st_buy_matrix.columns',st_buy_matrix.shape[1])
        st_buy_matrix = np.column_stack((st_buy_matrix,choose_matrix1[:,[15,16,17]]))
        print('st_buy_matrix.columns',st_buy_matrix.shape[1])
        st_buy_matrix = np.column_stack((st_buy_matrix,choose_matrix1[:,[2]]))
        print('st_buy_matrix.columns',st_buy_matrix.shape[1])
        st_buy_matrix = np.column_stack((st_buy_matrix,choose_matrix1[:,[10]]))
        print('st_buy_matrix.columns',st_buy_matrix.shape[1])
        st_buy_matrix = np.column_stack((st_buy_matrix,choose_matrix1[:,[4,12,11,21]]))
        print('st_buy_matrix.columns',st_buy_matrix.shape[1])
        
        '''之后如果要加上动态选股的，则把前面的加上 把下面这句话去掉。'''
        buy_matrix = st_buy_matrix

        #选股的股票应该和买入的股票一样吗?
        '''排除今天卖出的股票
        可能前面一天没有文件 第一天 有则去除昨天买入的股票'''
#        try:
#            day_before = date_list[j-1]
#            print (day_before)
#            #读之前买入的文件
#            df_buy_before = pd.read_csv(data_file + '/' + str(day_before.date()) + '.csv')
#            df_buy_before['code'] = df_buy_before['code'].apply(lambda x:str(x).zfill(6))
#            print ('Before com: shape:%d' % buy_matrix.shape[0])
#            buy_matrix = buy_matrix[np.in1d(buy_matrix[:,1],df_buy_before['code'].values,invert=True)]
#            print ('After com: shape:%d' % buy_matrix.shape[0])
#            print ('buy_matrix.shape:%d' % buy_matrix.shape[0])
#        except:
#            pass
        
        '''
        同一个日期是同时进行股票的选股，买入和卖出的
        比如1月2号既要选股又要买入又要卖出
        买入的是昨天选的股票，卖出的是前天选出的股票
        1月2号选的股要在1月3号买入，在1月4号卖出

        特殊日期 买入后股票开盘涨停的卖出日期 不能在当天买入
        比如：1月2号买入的股票在1月3号开盘涨停了，就不能在1月3号再买入了

        special_df 记录了会买入的而且有卖出当天开盘涨停的股票 code day_aftertomo
        '''
        sp_tmp = special_df[special_df['day_aftertomo'] == day] #会在卖出当天开盘涨停的股票

        '''
        numpy库下的in1d函数:在序列B中寻找与序列A相同的值，并返回一逻辑值（True,False）或逻辑值构成的向量。
        notes:当invert=True时，两个序列不相同的部分为true，相同的部分则为false
        '''
        buy_matrix = buy_matrix[np.in1d(buy_matrix[:,1],sp_tmp['code'].values,invert=True)]#去除掉今天开盘涨停的股票
        print ('buy_matrix.columns' ,buy_matrix.shape[1])
        try:
            df_buy = pd.DataFrame(buy_matrix,columns=['datetime','code','buy','buyPolicy','policy4_std', 'policy4_value', 'policy5_value', 'buy_open', 'buy_low', 'buy_high', 'st_or_dy',\
                                                      'after_sign','day_tomo','day_aftertomo','totals1','settlement', 'open', 'mean_value2_hl_before', '30_close_highest','close'])
        except ValueError:  #经过这个筛选之后就没有值存在 所以证明当天选的都有问题 直接跳过
            if signal == 1:
                count += 1
            pro_test.append([day,0,advanced_signal,signal,pro_sum,high_count,count,min_stock_num,0,0,0])
            pro_list.append(0)
            j += 1
            continue
        #print (df_buy.info())
        df_buy['buy'] = df_buy['buy'].astype(float)
        
        '''
        对选股的买入价格进行筛选 
        并且转化为卖出需要的格式 
        'code','buy','after_sign','day_tomo','day_aftertomo','totals1','settlement'
        并且增加 有买入后一字涨停的股票的 code和day_aftertomo信息 到special_df
        如果通过买入价格筛选之后没有股票了，便将今天的利润记为0， continue
        '''
        df_buy1 = df_buy[~np.isnan(df_buy['buy'])][['code','buy','after_sign','day_tomo','day_aftertomo','totals1','settlement']]
#        #对买入价进行筛选
#        df_buy1 = df_buy1[df_buy1['buy']>price_down]
#        df_buy1 = df_buy1[df_buy1['buy']<price_up]

        #after_sign 是表示卖出当天开盘涨停 不能卖出 得再过一个交易日卖出?
        add_sp_df = df_buy1[df_buy1['after_sign']==1][['code','day_aftertomo']]
        special_df = pd.concat([special_df,add_sp_df])

        #print (df_buy1.info())
        #numpy创建的数组都有一个shape属性，它是一个元组，返回各个维度的维数,[0]代表行数，[1]代表列数
        m = df_buy1.shape[0]
        if (m==0):
            print ('After filter from buy price, there is no stock exist!')
            if signal == 1:
                count += 1
            pro_test.append([day,0,advanced_signal,signal,pro_sum,high_count,count,min_stock_num,0,0,0])
            j += 1
            pro_list.append(0)
            continue
        buy_matrix = df_buy1.values
             
        '''
        卖出股票 记录卖出股票所耗时间 
        另外 可能分钟数据缺失 导致卖出数据缺失 --直接去掉
        如果由于数据缺失导致df_sell没有值，pro=0 continue
        df_day  格式：'datetime','code','buy','buyPolicy','policy4_std', 'policy4_value', 'policy5_value', 
        'buy_open', 'buy_low', 'buy_high', 'st_or_dy','totals1',
        'settlement', 'open', 'mean_value2_hl_before', '30_close_highest','close','sell','SellPolicy','sell_lb',
        'sell_ub','max_p','min_p','f_p','open_p'
        '''
        start1 = time.perf_counter()     
        df_sell = sell_result_update_ver2(buy_matrix,day,day_after,m,a_up1001,a_up1002,b_up100,sell_minute,c)  
        print(df_sell.shape)
        df_sell.dropna(how='all',inplace=True)
        end1 = time.perf_counter()
        print ('To get sell result -- Time cost:')
        print (str(end1-start1))
        try:
            df_sell['code'] = df_sell['code'].apply(lambda x:str(int(x)).zfill(6))
        except ValueError:
            print ('df_sell no value!!')
            print (df_sell.info())
            print (df_sell.head())
            print (df_sell[np.isnan(df_sell['code'])])
        try:
            df_buy['code'] = df_buy['code'].apply(lambda x:str(int(x)).zfill(6))
        except ValueError:
            print ('df_buy no value!!')
            print (df_buy.info())
            print (df_buy.head())
            print (df_buy[np.isnan(df_buy['code'])])
            
        try:
            df_day = pd.merge(df_buy, df_sell, on=['code'], how='left')
        except ValueError:
            print ('df_buy')
            print (df_buy)
            print ('df_sell')
            print (df_sell)
            if signal == 1:
              count += 1
            pro_test.append([day,0,advanced_signal,signal,pro_sum,high_count,count,min_stock_num,0,0,0])
            j += 1
            pro_list.append(0)
            sell_error.append(day)
            continue
            
        #属性中的datetime是指 买入股票的日期
        df_day['buy'] = df_day['buy'].apply(lambda x:float('%.2f' % x))
        df_day['sell'] = df_day['sell'].apply(lambda x:float('%.2f' % x))
        df_day['datetime'] = df_day['datetime'].apply(lambda x:x.date())
        df_day['profit'] = (df_day['sell']-df_day['buy'])/df_day['buy']-0.002
        df_day['pro_bc'] = (df_day['close']-df_day['buy'])/df_day['buy']
        df_day['pro_bc1'] = df_day['pro_bc'] -0.002
        df_day = df_day.drop(['after_sign','day_tomo','day_aftertomo'],axis=1)
        df_day1 = df_day[np.isnan(df_day['sell']).apply(lambda x:not x)]
        j += 1
        buy_num = df_day1.shape[0]
        all_num = df_day.shape[0]
        
        '''预警机制   
        预警机制（增加动态增长情况和禁忌操作）：
        min_stock_num初始化为10
        遇到当天卖出股票收益（每支股的收益-成本0.002的平均值）<0且选出股票数<=10则进入警戒状态, 但是如果遇到选出的股票数大于min_stock_num时，
        则买入当天跳出警戒状态，min_stock_num重新初始化为10，并且如果连续警戒状态天数超过5天，min_stock_num动态增长，变为15，
        即之后大于15才能跳出警戒状态
        禁忌操作：就是如果是当天 由选股数量由警戒状态变为非警戒状态 则当天 不会重新进入警戒状态
        警戒状态：当选出股票数<min_stock_num时，直接不买入

        高级预警机制：
        在基本预警机制的基础上，如果连续两天的利润之和<-5%则进入高级预警状态，进入高级预警状态之后模拟买入，
        遇到模拟利润--（这里有点问题，收盘市值相比？）
        大于0（这时候基本预警机制还是存在的，即每一天先判断是否符合基本预警机制，
        如果signal=0才属于模拟的时候）的时候跳出高级预警状态，跳出高级预警之后的三天内遇到选出股数小于8模拟操作，
        不进行真实购买（这是仍要判断是否符合基本的预警机制）。
        即我们的高级预警机制是以基本预警机制为基础的，同时即使处在高级预警状态或者其延长期，我们仍要判断是否符合基本预警。
        '''
        
        '''
        存在高级预警
        '''
        #pro_list record the pro of day
        pro_yester = 0
        if (len(pro_list)<=1):
            #pro_sum 记录前两天的利润之和 用于高级预警状态
            pro_sum = sum(pro_list)
            #pro_yester 记录前一个交易日的利润 用于普通预警
            pro_yester = sum(pro_list)
        elif (len(pro_list)<=2):
            pro_sum = sum(pro_list)
            pro_yester = pro_list[-1]
        else:
            pro_sum = pro_list[-1]+pro_list[-2]
            pro_yester = pro_list[-1]
        
            
        #使用收盘的价值来计算
        #本来没有预警  要先判断是否会出现高级预警
        if (signal==0):
            if pro_sum <-0.05:
                advanced_signal = 1
            else:
                pass
            if (advanced_signal==1):#模拟 不真正买入
                #在高级预警状态 仍然得判断 是不是会引发普通预警
                
                if (df_day.shape[0]<=min_stock_num)&(pro_yester<0):#会出现普通预警
                    signal = 1
                    count +=1
                    f.write(str(day.date()))
                    f.write('        Change signal 0--1,出现高级预警[前两天的利润之和 < -0.05],pro_sum = '+ str(pro_sum))
                    f.write('        也出现普通预警：')
                    f.write('连续两个交易日选出股票数<=5,df_day.shape[0] = '+str(df_day.shape[0]))
                    f.write(';')
                    f.write('前一个交易日的利润<0,pro_yester = '+str(pro_yester))
                    f.write('\n')
#                   if day == pd.to_datetime('20190605'):
#                         f.write('20190605 df_day.shape:')
#                         f.write(df_day.shape[0])
#                         f.write('\n')
                    
                else:#不会出现预警
                    signal = 0
                    count = 0
                if np.isnan(np.mean(df_day['pro_bc'])):#选了一支股 没有买入
                    pro_test.append([day,0,advanced_signal,signal,pro_sum,high_count,count,min_stock_num,buy_num,all_num,pro_yester])
                    pro_list.append(0)
                    continue
                else:
                    pro_test.append([day,pro_yester,advanced_signal,signal,pro_sum,high_count,count,min_stock_num,buy_num,all_num,pro_yester])
                    pro_list.append(np.mean(df_day['pro_bc']))
                    if pro_yester > 0:
                        advanced_signal = 0
                        high_count = 0
                        f.write(str(day.date()))
                        f.write('In advance，[出现了高级预警，前两天的利润之和 < -0.05]，没有出现普通预警')
                        f.write('        high_count=0')
                        f.write('前两个交易日的利润之和 = '+str(pro_sum))
                        f.write('\n')

                    else:
                        pass
                

                    
            else:#没有进入高级预警状态
                if ((high_count < 3)&(df_day.shape[0]<=8)):#处于高级预警的影响范围 如果选股数量<8则模拟买入 不真实操作
                     if np.isnan(np.mean(df_day['pro_bc'])):
                        pro_test.append([day,0,advanced_signal,signal,pro_sum,high_count,count,min_stock_num,buy_num,all_num,pro_yester])
                        pro_list.append(0)
                        continue
                     else:
                        pro_test.append([day,np.mean(df_day['pro_bc']),advanced_signal,signal,pro_sum,high_count,count,min_stock_num,buy_num,all_num,pro_yester])
                        pro_list.append(np.mean(df_day['pro_bc']))
                    #模拟买入 仍要判断会不会进入预警
                     if (df_day.shape[0]<=min_stock_num)&(pro_yester<0):#会出现普通预警
                         signal = 1
                         count +=1
                         f.write(str(day.date()))
                         f.write('       Change signal 0--1，普通预警[处于高级预警的范围]')
                         f.write('\n')
                     else:#不会出现预警
                         signal = 0
                         count = 0
                #不处于高级预警的影响范围
                else:
                    #买入股票信息写入文件
                    df_day.to_csv(data_file + '/' + str(day.date()) + '.csv', index=False)
                    df_day_earn = df_day[df_day['profit']>0]
                    df_day_lose = df_day[df_day['profit']<0]
                    final_choose_df = pd.concat([final_choose_df,df_day])
                    final_earn_df = pd.concat([final_earn_df,df_day_earn])
                    final_lose_df = pd.concat([final_lose_df,df_day_lose])
                    signal = 0
                    count = 0
                    
                    if np.isnan(np.mean(df_day['profit'])):
                        print ('Actually choose and buy /sell but there is nan data in profit.')
                        print (df_day['profit'])
                        pro_test.append([day,0,advanced_signal,signal,pro_sum,high_count,count,min_stock_num,buy_num,all_num,pro_yester])
                        pro_list.append(0)
                        continue
                    else:
                        pro_test.append([day,np.mean(df_day['pro_bc']),advanced_signal,signal,pro_sum,high_count,count,min_stock_num,buy_num,all_num,pro_yester])
                        pro_list.append(np.mean(df_day['pro_bc']))
                        
                    if (df_day.shape[0]<=min_stock_num)&(pro_yester<0):#第二天会出现预警
                        signal = 1
                        count += 1
                        f.write(str(day.date()))
                        f.write('        Change signal 0--1，出现普通预警，不在高级预警的范围')
                        f.write('\n')
                    else:#不出现预警
                        signal = 0
                        count = 0
                        
        else:#本来处于预警期 
            if (df_day.shape[0]>min_stock_num):#出现大于5的 预警消除 前一天便可以判断 相当于早上判断这个 可是一天过完之后还是得判断会不会进入预警期
                signal = 0
                if advanced_signal == 0:
                    df_day.to_csv(data_file + '/' + str(day.date()) + '.csv', index=False)
                    df_day_earn = df_day[df_day['profit']>0]
                    df_day_lose = df_day[df_day['profit']<0]
                    final_choose_df = pd.concat([final_choose_df,df_day])
                    final_earn_df = pd.concat([final_earn_df,df_day_earn])
                    final_lose_df = pd.concat([final_lose_df,df_day_lose])
                    f.write(str(day.date()))
                    f.write('          Change signal 1--0，本来处于预警期，但连续两个交易日选出的股票数>5,预警消除')
                    f.write('\n')
                    #重新初始化
                    min_stock_num = init_min_stock_num
                    count = 0
                    if np.isnan(np.mean(df_day['pro_bc'])):
                        pro_test.append([day,0,advanced_signal,signal,pro_sum,high_count,count,min_stock_num,buy_num,all_num,pro_yester])
                        pro_list.append(0)
                        continue
                    else:
                        pro_test.append([day,np.mean(df_day['pro_bc']),advanced_signal,signal,pro_sum,high_count,count,min_stock_num,buy_num,all_num,pro_yester])
                        pro_list.append(np.mean(df_day['pro_bc']))
                #本来就处于高级预警状态
                else:
                    if np.isnan(np.mean(df_day['pro_bc'])):
                        pro_test.append([day,0,advanced_signal,signal,pro_sum,high_count,count,min_stock_num,buy_num,all_num,pro_yester])
                        pro_list.append(0)
                        continue
                    else:
                        pro_test.append([day,np.mean(df_day['pro_bc']),advanced_signal,signal,pro_sum,high_count,count,min_stock_num,buy_num,all_num,pro_yester])
                        
            else:
                count += 1
                pro_test.append([day,np.mean(df_day['pro_bc']),advanced_signal,signal,pro_sum,high_count,count,min_stock_num,buy_num,all_num,pro_yester])
            
        if (count == 6):
            min_stock_num += 5
        else:
            pass
                
    '''先判断利润是否足够大 如果足够大 再进行存储'''
    try:
        data = final_choose_df[['code','datetime','buy','sell','st_or_dy']]
    except KeyError:
        return None
    #data['date'] = data['date'].apply(lambda x:return_datetime(x))
    data.set_index('datetime',inplace=True)
    data.sort_index(inplace=True)
    data['num'] = 1     #默认每只一份钱，留了个空位以防万一之后每只股票买的数量不一样多
    #print(data.head())

    result_real_pro,data_file = get_profit_update(data_path,sp,limit,data)
    l = result_real_pro.shape[0]
    #print (result_real_pro)
    
    #d_length为date_list的长度
    print ('Final result : %f' % result_real_pro.iloc[l-1].loc['real_profit'])
    #if (result_real_pro.loc[l-1,'real_profit'] >= limit) & (l>(d_length//8)):
    if (result_real_pro.iloc[l-1].loc['real_profit'] >= limit):
        final_choose_df.to_csv(data_file + '/' + 'choose.csv',index=False)
        pro_df = pd.DataFrame(pro_list,columns=['pro'])
        pro_df.to_csv(data_file + '/' + 'pro_test.csv',index=False)
        pro_df1 = pd.DataFrame(pro_test,columns=['date','pro','advanced_level','signal','pro_sum','high_count','count','min_stock_num','buy_num','all_num','pro_yester'])
        pro_df1.to_csv(data_file + '/' + 'pro_test_date.csv',index=False)
        
        special_df.to_csv(data_file + '/special.csv')
    
        result_real_pro.to_csv(data_file + '/real_pro.csv',index=True)
        
        result_real_pro.rename(columns={'real_profit':('rp' +'-' + sp)},inplace=True)
        show = result_real_pro['rp' +'-' + sp]
        
        return show
    else:
        return pd.Series()


def get_profit_update_with_price_limit(data_file,dataset):
    data = dataset[['code','buy','sell','st_or_dy','num']]
    print (data.shape)
    #有些静态选入的股票 并没有买入 所以要去除这一部分
    data.buy = data.buy.astype(float)
    data.st_or_dy = data.st_or_dy.astype(int)
    #data是算所有选入的股票 data1是算所有买入的股票
    data1 = data[np.isnan(data['sell']).apply(lambda x:not x)]
    print (data.shape)
    #cost是每股的成本的百分比
    cost = 0.002
    #这里收益指的是收益率，由于相当于用同样的钱去买每只股，故收益率可以简单平均
    data1['profit'] = (data1['sell'] - data1['buy'])/data1['buy'] - cost
    
    result_all = data.groupby(data.index).sum()
    
    result_buy_count = data1.groupby(data1.index).sum()
    result_buy = data1.groupby(data1.index).mean()
    result_buy['NotBuyNum']  = result_all['num'] - result_buy_count['num']
    result_buy['buy_num'] = result_buy_count['num']
    result_buy['all_num'] = result_all['num']
    result_buy['not_buy_rate'] = result_buy['NotBuyNum']/result_buy['all_num']
    result_buy['buy_rate'] = result_buy['buy_num']/result_buy['all_num']
    
    days = result_buy.shape[0]
    pro = np.zeros(days)
    diff = np.zeros(days)
    pro[0] = 100 + result_buy.iloc[0].loc['buy_num']*max_stock_pay*(result_buy.iloc[0].loc['profit'])
    diff[0] = 0
    for i in range(1,days):
        
        #有价格限制
        if (pro[i-1]/result_buy.iloc[i].loc['all_num']>max_stock_pay):
            pro[i] = pro[i-1] + result_buy.iloc[i].loc['buy_num']*max_stock_pay*(result_buy.iloc[i].loc['profit'])
        else:
            pro[i] = pro[i-1]*result_buy.iloc[i].loc['not_buy_rate'] + pro[i-1]*result_buy.iloc[i].loc['buy_rate']*(result_buy.iloc[i].loc['profit']+1)
        diff[i] = np.abs(pro[i]-pro[i-1])
    
    result_buy['real_profit'] = pro
    result_buy['diff'] = diff
    
    #增加大盘的信息
    hs_df = pd.read_csv('E:/pyWorkspace/QI'+'/data/StockInfo/hs300_price.csv')
    hs_df['trade_date'] = hs_df['trade_date'].apply(lambda x:datetime.datetime.strptime(str(x), "%Y%m%d"))
    hs_df1 = hs_df[['trade_date','close']]
    hs_df1.rename(columns={'trade_date':'date'},inplace=True)
    result_buy.reset_index(inplace=True)
    result_buy['date'] = result_buy['date'].apply(lambda x:return_datetime_final(str(x)))
    result_buy = pd.merge(result_buy,hs_df1,on=['date'],how='left')
    result_buy.set_index(['date'],inplace=True)
    
    Data = result_buy[['profit','real_profit','buy_num','all_num','diff','close']]
    Data = Data.astype(float)
    Data['profit'] = Data['profit']*1000
    Data['diff'] = Data['diff']*10
    Data['close'] = (Data['close']-3000)/10
    Data.plot(figsize=(16,12))
    plt.grid(True)
    
    plt.savefig(data_file + '/' + 'profit_num_with_price_limit_add_index' + '.png',dpi = 400,bbox_inches='tight')
    plt.show()
    
    Num = result_buy[['buy_num','all_num']]
    #Num['st_num'] = result['num'] - result['st_or_dy']
    Num = Num.astype(float)
    Num.plot(figsize=(16,12))
    plt.grid(True)
    plt.savefig(data_file + '/' + 'num_with_price_limit_add_index' + '.png',dpi = 400,bbox_inches='tight')
    plt.show()
    return result_buy
    
print('初始化分时数据和日线数据路径')
#fenshi_path = 'E:/Stock/最新代码/Agu/Agu/ParaFindData/ParaFindData/fenshi_stocks.csv'
#daily_path = 'E:/Stock/最新代码/Agu/Agu/ParaFindData/ParaFindData/daily_stocks.csv'
#2019/11/01-2020/04/30
fenshi_path = 'F:/SmartLab/stockData/20200101_20201101/fenshi/fenshi_after_fq_0101_1101.csv'
daily_path = 'F:/SmartLab/stockData/20200101_20201101/daily_stocks.csv'
#data_path = root_file + '/data/1718-Result-Arrage/Test/'
data_path = 'F:/SmartLab/stockData/20200101_20201101/results-0201-1101/'
print('创建策略参数文件夹')
mkdir(data_path)

#获取日线的数据
'''
final_matrix格式
        'datetime'-0, 'code'-1, 'totals1'-2, 'policy3'-3, 'open'-4, 'high'-5,
       'mean_value4_before'-6, 'policy1', 'policy2', 'tr_before', 'settlement',
       '30_close_highest', 'mean_value2_hl_before'-12, 'low', 'top10sh',
       'after_sign', 'day_tomo', 'day_aftertomo', 'cp_sum', 'cq_sign',
       'mean_value_oc_before'-20,'close'
       含义
       今日时间、股票编码、总市值、前两天涨幅、今日开盘价格、今日最高价格、
       昨日四种价格平均所得的均价、收盘与30天最高收盘价差比例、成交量比例、昨日换手率、昨日收盘价格、
       30天最高收盘价、昨日最高最低价格平均所得的均价、今日最低价格、十大股东占比、
       之后一字涨停标志（如果一字涨停得下一个交易日卖出）、下一个交易日日期、下下个交易日日期、前五天涨幅之和、是否除权标志
       昨日开盘收盘价格平均所得的均价、今日收盘价格
(均价数据中暂时只使用了 'mean_value2_hl_before'，所以另外两列均价数据可以随意一点。)
'''
#print('内存有限，先测2019-06-01之前的')
#0101-1001 2020
print('开始读取日线数据')
start_date = '2020-02-01'
end_date = '2020-11-01'
fill_date = '2020-11-01'
final_df = pd.read_csv(daily_path) #DataFrame
#print(type(final_df),final_df.index)
#print(type(final_df))
#print(final_df)

final_df['day_tomo'].fillna(fill_date,inplace=True)
final_df['day_aftertomo'].fillna(fill_date,inplace=True)
#过滤掉688开头的股票
final_df = final_df[(final_df['code']<688000) | (final_df['code'] >= 689000)]
print('过滤后的股票代码',final_df['code'])

#final_df = final_df[final_df['datetime']>=start_date]
#final_df = final_df[final_df['datetime']<end_date]
final_df['code'] = final_df['code'].apply(lambda x:str(x).zfill(6))

final_df['datetime'] = final_df['datetime'].apply(lambda x:return_datetime(x))
#print ('日线数据：',final_df)
final_df['day_tomo'] = final_df['day_tomo'].apply(lambda x:return_datetime(x))
final_df['day_aftertomo'] = final_df['day_aftertomo'].apply(lambda x:return_datetime(x))
final_df['policy3'] = final_df['policy3']*100
final_df['totals1'] = final_df['totals1']/10000
#final_df.to_csv(root_file + '/data/Year180726To170526/final_features_use.csv', index=False)
##老版本pandas的df.as_matrix()改写成新版本pandas的df.values
final_df_copy = final_df  
final_matrix = final_df.values
print("type(final_matrix)",type(final_matrix))
#print("日线数据top10-14,",final_matrix[:,14])
date_list = sorted(np.unique(final_matrix[:,0]))
#date_list.append(pd.to_datetime('2019-07-05'))
d_length = len(date_list)
print ('股票日期:',date_list)

#final_matrix = final_df_copy

print('读取分时数据')
#获取分时数据
fenshi_df = pd.read_csv(fenshi_path) #DataFrame
#过滤掉688开头的股票
fenshi_df = fenshi_df.loc[(fenshi_df['code']<688000 )| (fenshi_df['code'] >=689000) ]
print('过滤后的股票代码',fenshi_df['code'])
#fenshi_df = fenshi_df[fenshi_df['date'] >= start_date]
#fenshi_df = fenshi_df[fenshi_df['date']<end_date]
#print('分时数据时间',fenshi_df['datetime'])
fenshi_df['code'] = fenshi_df['code'].apply(lambda x:str(x).zfill(6))
fenshi_df['datetime'] = fenshi_df['datetime'].apply(lambda x:to_datime(x))
#fenshi_df['date'] = fenshi_df['date'].apply(lambda x:return_datetime(x))
#datetime 变为 timestamp形式
fenshi_df['date'] = pd.to_datetime(fenshi_df['date'])
fenshi_df = fenshi_df[['datetime','code','open','close','high','low','date','time']]

##获取大盘数据
#index_df = pd.read_csv('D:/Stock/Data/190101_191022/index_info.csv')
#index_df['trade_date'] = index_df['trade_date'].apply(lambda x:MarketToTime(x))
##index_df['trade_date'] = pd.to_datetime(index_df['trade_date'])
#index_df = index_df[['trade_date','indexUse1']]

'''
Func:maxDrawDown -- return the max drawdown
Input:
    arr -- profit_array
Output:
    num - maxDrawDown
'''
def maxDrawDown(arr):
    i = np.argmax(np.maximum.accumulate(arr) - arr)
    j = np.argmax(arr[:i])
    return (arr[j] - arr[i])

'''
Func:one_neigh -- return the 3 para lists which change one para from origin para_list
Input:
    para_list -- whole para lists
    para -- the origin para list
Output:
    return_para - list of para_list which change a para randomly
'''
def one_neigh(para_list,para):
    a = np.random.randint(0,len(para))
    return_para = []
    for i in sample(para_list[a],3):
        tmp_list = para.copy()
        tmp_list[a] = i
        return_para.append(tmp_list.copy())
    return return_para

def random_choose(para_list):
    r_para = []
    for i in para_list:
        r_para.append(sample(i,1)[0])
    return r_para

'''
Func:dist -- make disturbution to avoid local best
Input:
    para_list -- whole para lists
Output:
    para - choose every para randomly
'''
def dist(para_list):
    para = []
    for i in para_list:
        a = sample(i,1)[0]
        para.append(a)
    return para

if __name__ == '__main__':
    print('进入main函数:')
    final_show_df = pd.DataFrame()
    #如果收益最后没达到这个值 不保存过程中间的文件
    limit = 70 #本来是70 万
    #time库在更新中舍弃了time.clock() 换成了time.perf_counter()
    start = time.perf_counter()
    best_pro = 0
    best_para = []
    
    pro_list = []
    para_change_list = []
    count = 0
    
    para_col = [policy1_list,policy2_list,policy3_list,tr_list,cp_up_list,cp_down_list,top10sh_list,totals1_down_list,totals1_up_list,\
                   price_up_list,price_down_list,a_up1001_list,a_up1002_list,b_up100_list,c_list,\
                   qu_num_list,mulh_num_list,settle_num_list,min_stock_num_list,sell_minute_list]
    
    tabu_list = pd.Series([0 for i in range(len(para_col))])
    
    #ver1901-1907-0.03-1.0-10-2-8-4-50-30-300-40-4--0.001--0.001-0.07-0.082-0.96-0.96-1-9-600
    para_good = [0.03,1,10,2,8,4,50,30,300,40,4,-0.001,-0.001,0.07, 0.082,0.96,0.96,1,5,600]
    print('根据参数信息选取股票...')
    #测试特定参数（现在用的参数）的结果
    result = make_stock_result_with_advanced_num(para_good,0,0.18)
    #result = make_stock_result_with_advanced_num(para_good,100,0.18)
    print('获取股票end')
#给定参数空间最好值
'''
    for i in range(1000):
        para = random_choose(para_col) #随机获取一组参数值
        #输出para
        print("para random_choose",para)
        result = make_stock_result_with_advanced_num(para,limit,0.18)
        try:
            tmp_pro = result[len(result)-1]
            limit  = tmp_pro
        except IndexError:
            continue
        Maxdd = maxDrawDown(result)
        print (Maxdd)
        #以得到利润减去最大回撤为评判标准
        tmp_pro = tmp_pro-Maxdd
        if tmp_pro > best_pro:
            para_good = para.copy()
            best_para = para
            best_pro = tmp_pro
            limit = best_pro
            pro_list.append(best_pro)
            para_change_list.append(best_para.copy())
            print (best_pro)
            print (best_para)
        
    lately_choose = []
    #记录参数变化状况的list
    para_tmp = []
    iter_count = 0
    t_para = best_para.copy()
    
    while (best_pro <= 160)&(count < 40):
        
        #count 为选择邻域次数
        count += 1
        print ('***********************count**************************')
        print (count)
        iter_para = best_para.copy()
        
        #邻域结构就是 中间两个随机选取的参数变动得到的所有参数组合
        para_change = sample(range(len(para_col)),2)
        while ((para_change[0] in lately_choose) | (para_change[1] in lately_choose) | \
        ((tabu_list[para_change[0]] + tabu_list[para_change[1]])>10)):
            para_change = sample(range(len(para_col)),2)
            
        f = para_change[0]
        s = para_change[1]
        
        #增加禁忌 使得上一次随机到的组合不再随机到
        #随机到次数组合多的不再 选中
        lately_choose = para_change
        tabu_list[f] += 1
        tabu_list[s] += 1
        
        try:
            print (t_para[f])
        except IndexError:
            t_para = para.copy()
        for para1 in  para_col[f]:
            t_para[f] = para1
            for para2 in para_col[s]:
                t_para[s] = para2
                para_tmp.append(t_para.copy())
        print (len(para_tmp))
        
        #如果在邻域空间中搜索100次还没有任何改进 放弃该邻域空间 para_tmp存放所有的邻域结构
        count_inside = 0
        signal = 0
        for i in para_tmp:
            #print (i)
            if ((count_inside>80) &(signal == 0)):
                break
            count_inside += 1
            result = make_stock_result_with_advanced_num(i,limit,0.18)
            try:
                tmp_pro = result[len(result)-1]
                limit = tmp_pro
            except IndexError:
                continue
            Maxdd = maxDrawDown(result)
            print (Maxdd)
            tmp_pro = tmp_pro-Maxdd
            if tmp_pro > best_pro:
                print (tmp_pro)
                best_para = i
                best_pro = tmp_pro
                pro_list.append(best_pro)
                para_change_list.append(best_para.copy())
                signal = 1
                iter_count = 0
        t_para = best_para.copy()
        if iter_para == best_para:
            iter_count += 1
        #5次没有改进 便认为到了局部最优解 进行扰动
        if (iter_count >= 5):
            tabu_list = pd.Series([0 for i in range(len(para_col))])
            t_para = dist(para_col)
    
    #print (results)
    end = time.perf_counter()
    print (str(end-start))
    para_change_df = pd.DataFrame(para_change_list)
    para_change_df.to_csv(data_path + 'para_change.csv')
    tmp_name = 'ver20200101-20201001'
    for i in best_para:
        tmp_name = tmp_name+'-'+str(i)
    os.renames(data_path + tmp_name,data_path + 'Best-'+tmp_name)
'''