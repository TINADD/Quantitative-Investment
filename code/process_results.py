#process results
import os
import pandas as pd 
import numpy as np
import matplotlib.pyplot as plt

data_path = 'F:/SmartLab/stockData/20200101_20201101/1214-results-0101-1201-num5/'
result_pro =  pd.read_csv(data_path + 'real_pro.csv')

'''
result_pro.loc[0,'real_profit'] = 100 + 100*result_pro.iloc[0].loc['buy_rate']*(result_pro.iloc[0].loc['profit'])
result_pro.loc[0,'diff'] = 0
days = len(result_pro)
print('days = ',days)

for i in range(1,days):
    #没有价格限制
    result_pro.loc[i,'real_profit'] = result_pro.iloc[i-1]['real_profit'] * result_pro.iloc[i].loc['not_buy_rate'] + \
        result_pro.iloc[i-1]['real_profit']*result_pro.iloc[i].loc['buy_rate']*(result_pro.iloc[i].loc['profit']+1)
    result_pro.loc[i,'diff'] = np.abs(result_pro.iloc[i]['real_profit'] - result_pro.iloc[i-1]['real_profit'] )

result_pro.to_csv(data_path + 'new_result_pro.csv',index=False)
'''
result_pro.set_index('datetime',inplace=True)
#result_pro.sort_index(inplace=True)

Data = result_pro[['profit','real_profit','buy_num','all_num','diff']]

Data = Data.astype(float)
Data['profit'] = Data['profit']*1000
Data['diff'] = Data['diff']*10

Data.plot(figsize=(16,12))
plt.grid(True)

plt.savefig(data_path +  'new_profit_num_add_index' + '.png')
