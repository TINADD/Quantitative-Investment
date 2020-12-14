#pandas处理日期，按照日期筛选
import pandas as pd

daily_path = ""
fenshi_path = ""

new_daily_path = ""
new_fenshi_path = ""


start_date = '20200101'
end_date = '20200201'
start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

#读文件
daily_df = pd.read_csv(daily_path)

#整理数据
#将数据类型转换为日期类型
daily_df['datetime'] = pd.to_datetime(daily_df['datetime'])
con1 = daily_df['datetime']>=start_date
con2 = daily_df['datetime']<=end_date

new_daily_df = daily_df[con1 & con2]
new_daily_df.to_csv(new_daily_path,index=False)

fenshi_df = pd.read_csv(fenshi_path)
fenshi_df['date'] = pd.to_datetime(daily_df['date'])
con1 = fenshi_df['date']>=start_date
con2 = fenshi_df['date']<=end_date

new_fenshi_df = fenshi_df[con1 & con2]
new_fenshi_df.to_csv(new_fenshi_df,index=False)
