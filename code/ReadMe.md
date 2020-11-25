程序清单说明

getfq_fenshi.py：对分时数据进行复权处理

concat_fenshi.py：对两个文件的分时数据进行拼接并进行复权处理

get_top10.py：获取给定时间段的十大股东数据

get_top10_basedDaily：根据日线数据的日期获得对应的十大股东数据

Get_dealed_daily_data_hldiff -noDown.py：对下载好的原始日线数据进行处理

Get_dealed_daily_data_hldiff：下载日线数据和复权因子，并对日线数据进行复权处理

get_minute_data.py：获取分时数据，得到的是未复权处理的，需要进行复权处理才能供search_best_para_test.py使用

search_best_para_test.py：对下载的日线数据和分时数据进行模拟测试，获得对应的选股买卖数据；包括调参代码，选一组最好的参数用来测试日线数据和分时数据

update_stock_everyday.py：用来进行每日交易，测试用不到这个程序

debug_python.py：调试过程中遇到的问题及解决方法，算是一个学习笔记

#规定下载的日线+分时+复权数据的存储目录

E:\Stock\Data\start_date-end_date\

#十大股东数据和上述程序在同一目录下

#测试结果的存储目录

E:\Stock\Results\start_date-end_date\