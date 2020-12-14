#change columns
import os
import tushare as ts
import pandas as pd
import datetime
import time
import numpy as np

start_date = '2020-11-06'
end_date = '2020-12-06'
st = '20201106'
et = '20201206'

#f:\SmartLab\Quantitative-Investment/stockdata/
data_path = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))+'/stockData/'

