import os
import tushare as ts
import pandas as pd
import datetime
import time
import numpy as np

#更新十大股东占比
#[ts_code,hold_ratio,top10_d_r] top10_d_r =hold_ratio
token = '92fa5b4defcb65d71defd90b46b240ad77860cc3c0ec0958e492172d'
ts.set_token(token)

pro = ts.pro_api()  #用来获取股票数据的对象

top10_holders_saved_path = "./" #数据保存在当前目录下
top10_holders = pro.top10_holders(ts_code='600000.SH',fields='ts_code,hold_ratio')
top10_holders['top10_d_r'] = top10_holders['hold_ratio']
top10_holders.to_csv(top10_holders_saved_path+"top10_1030.csv")