import os
import sys

print('os.getcwd : ',os.getcwd(),'\n') #os.getcwd :  C:\Users\PC\.leetcode
print('sys.path',sys.path) #sys.path ['f:\\SmartLab\\Quantitative-Investment\\code', 'E:\\github\\Stock\\EliteQuant_Python', 'E:\\pyWorkspace\\RL\\QI\\Marl_DailyStock', 'D:\\Anaconda\\Ana3\\Lib\\site-packages', 'C:\\Users\\PC\\.leetcode', 'E:\\Anaconda\\python38.zip', 'E:\\Anaconda\\DLLs', 'E:\\Anaconda\\lib', 'E:\\Anaconda', 'E:\\Anaconda\\lib\\site-packages', 'E:\\Anaconda\\lib\\site-packages\\win32', 'E:\\Anaconda\\lib\\site-packages\\win32\\lib', 'E:\\Anaconda\\lib\\site-packages\\Pythonwin']

cur_path = os.path.dirname(os.path.realpath(sys.argv[0]))
print(cur_path) #F:\SmartLab\Quantitative-Investment\code