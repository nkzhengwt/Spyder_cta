# -*- coding: utf-8 -*-
import pandas as pd

import numpy as np

import math

import datetime

import time

import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")

class Indicators():
    def __init__(self, dataframe, params = []):
#        dataframe = pd.read_csv(path,parse_dates=True)
        self.dataframe = dataframe
        self.params = params

        self.dataframe['return'] = 0
        for i in range(1,len(dataframe['return'])):
            #http://pandas.pydata.org/pandas-docs/stable/indexing.html#indexing-view-versus-copy
            dataframe.loc[i,'return'] = (self.dataframe.loc[i,'open']-self.dataframe.loc[i-1,'open'])/self.dataframe.loc[i-1,'open']
        self.Return = dataframe['return']
        self.dataframe['time'] = dataframe['tradeDate']
        self.dataframe['cumulative_return'] = self.dataframe['open']
        self.dataframe['cumulative_return'] = self.dataframe['cumulative_return']/self.dataframe.loc[0,'open']
        self.dataframe['cumulative_return'] = dataframe['cumulative_return']*1000000
        self.dataframe.index = pd.to_datetime(dataframe['tradeDate'])#!!!!!
        #分年计算
        self.year_slice = {}
        i = 0
        y = time.strptime(self.dataframe['time'].iat[0],"%Y-%m-%d").tm_year
        for j in range(1,len(self.dataframe)):
            if y != time.strptime(self.dataframe['time'].iat[j],"%Y-%m-%d").tm_year:
                self.year_slice[str(y)] = dataframe[i:j-1]
                y = time.strptime(self.dataframe['time'].iat[j],"%Y-%m-%d").tm_year
                i = j
        self.year_slice[str(y)] = dataframe[i:]
        '''
        plt.figure()
        i = 1
        for k in self.params:
            plt.subplot(2,2,i)
            i = i+1
            self.dataframe['asset'+ str(k)].plot()
        plt.subplot(2,2,i)
        self.dataframe['cumulative_return'].plot(x=None, y=None, kind='line', ax=None, subplots=False, sharex=None, sharey=False, layout=None, figsize=None, use_index=True, title=None, grid=None, legend=True, style=None, logx=False, logy=False, loglog=False, xticks=None, yticks=None, xlim=None, ylim=None, rot=None, fontsize=None, colormap=None, table=False, yerr=None, xerr=None, secondary_y=False, sort_columns=False)
        plt.show()
        '''


###年化收益
    def annual_return(self,asset,year):
        #替换self.dataframe为self.year_slice[year]
        #假设序列是按日为单位的。
        #假设把前一年的所有利润都投入下一年，且复利是按年计算。

        #年化收益开n次根以后有做年化处理吗？我没太理解代码的逻辑。一般我都是一年交易日数量计作244常数；

        R = self.year_slice[year][asset].iat[-1]/self.year_slice[year][asset].iat[0]
        t1 = time.strptime(self.year_slice[year]['time'].iat[0],"%Y-%m-%d")
        t2 = time.strptime(self.year_slice[year]['time'].iat[-1],"%Y-%m-%d")
        d1 = datetime.datetime(t1.tm_year, t1.tm_mon, t1.tm_mday)
        d2 = datetime.datetime(t1.tm_year, t2.tm_mon, t2.tm_mday)
        n = (d2-d1).days
        n = n/244
        return math.pow(R, 1/n)-1

###最大回撤
    def max_draw(self,asset,year):
        self.year_slice[year]['max'] = 0
        self.year_slice[year].ix[0,'max'] = self.year_slice[year].ix[0,asset]#loc, iloc, and ix
        for i in range(1, len(self.year_slice[year][asset])):
            if self.year_slice[year].ix[i, asset] > self.year_slice[year].ix[i-1, 'max']:
                self.year_slice[year].ix[i, 'max'] = self.year_slice[year].ix[i, asset]
            else:
                self.year_slice[year].ix[i, 'max'] = self.year_slice[year].ix[i-1, 'max']
        self.year_slice[year]['retreat']=(self.year_slice[year][asset]- self.year_slice[year]['max'])/self.year_slice[year]['max']
        #print(self.year_slice[year])
        return min(self.year_slice[year]['retreat'])*(-1)

###波动率
    def volatility(self,asset,year):
        #波动率和夏普这些都是要乘sqrt(244/length)的
        return np.std(self.year_slice[year][asset])*math.sqrt(244/len(self.year_slice[year][asset]))

###夏普比率
    def sharp(self, asset,no_risk_R,year):
        #波动率和夏普这些都是要乘sqrt(244/length)的
        return (self.annual_return(asset,year)-no_risk_R)/self.volatility(asset,year)*math.sqrt(244/len(self.year_slice[year][asset]))

###卡玛比率
    '''
    Calmar比率(Calmar Ratio) 描述的是收益和最大回撤之间的关系。计算方式为年化收益率与历史最大回撤之间的比率。
    '''
    def calmar(self,asset,year):
        #最大回撤取绝对值；这样calmar也是正值；
        return self.annual_return(asset,year)/self.max_draw(asset,year)

###日胜率
    def daily_win_ratio(self,asset,year):
        #df的条件选择不是self.dataframe[asset][self.dataframe[asset] > 0]而是self.dataframe[self.dataframe[asset] > 0][asset]
        #！！
        pnl = asset.replace('asset','pnl')
        n1 = len(self.year_slice[year][self.year_slice[year][pnl] > 0][pnl])
        n2 = len(self.year_slice[year][pnl])
        return n1/n2

###日盈亏比
    def win_lose_ratio(self,asset,year):
        self.year_slice[year]['dif'] = self.year_slice[year][asset] - self.year_slice[year][asset].shift(1)
        return abs(sum(self.year_slice[year][self.year_slice[year]['dif']>0]['dif']))/abs(sum(self.year_slice[year][self.year_slice[year]['dif']<0]['dif']))

###大回撤区间
    def worst_draw_interval(self,asset,year):
        self.year_slice[year]['max'] = 0
        self.year_slice[year].ix[0,'max'] = self.year_slice[year].ix[0,asset]
        self.year_slice[year]['max_time'] = self.year_slice[year]['time']
        for i in range(1, len(self.year_slice[year][asset])):
            if self.year_slice[year].ix[i, asset] > self.year_slice[year].ix[i-1, 'max']:
                self.year_slice[year].ix[i, 'max'] = self.year_slice[year].ix[i, asset]
            else:
                self.year_slice[year].ix[i, 'max'] = self.year_slice[year].ix[i-1, 'max']
                self.year_slice[year].ix[i, 'max_time'] = self.year_slice[year].ix[i-1, 'max_time']
        self.year_slice[year]['retreat']=(self.year_slice[year][asset]- self.year_slice[year]['max'])/self.year_slice[year]['max']
        max_draw = min(self.year_slice[year]['retreat'])

        data = self.year_slice[year][self.year_slice[year]['retreat'] == max_draw]
        t1 = data['tradeDate']#
        t2 = data['max_time']
        return t1,t2

###总换手
    def total_turnover(self,asset,year):
        #需要分析一下全年的换手情况和交易费用情况。
        turnover = asset.replace('asset','turnover')
        return sum(self.year_slice[year][turnover])

###日均换手
    def average_daily_turnover(self,asset,year):
        t1 = time.strptime(self.year_slice[year]['time'].iat[0],"%Y-%m-%d")
        t2 = time.strptime(self.year_slice[year]['time'].iat[-1],"%Y-%m-%d")
        d1 = datetime.datetime(t1.tm_year, t1.tm_mon, t1.tm_mday)
        d2 = datetime.datetime(t1.tm_year, t2.tm_mon, t2.tm_mday)
        n = (d2-d1).days
        return self.total_turnover(asset,year)/n

###日均持仓
    def average_daily_position(self,asset,year):
        #total总表的信息太少了，至少给出仓位（方向和手数）
        position = asset.replace('asset','position')
        return self.year_slice[year][position].mean()

###次均收益
    def minor_average_return(self,asset,year):
        #次均收益，这是每次交易的收益，是从这次换仓开始到下次换仓结束的，不能总收益直接除以天数，那成单利日均收益了
        position = asset.replace('asset','position')
        sum_pos = sum(self.year_slice[year][self.year_slice[year][position]!=0][position])
        num = len(self.year_slice[year][self.year_slice[year][position]!=0][position])
        return sum_pos/num

    def write_indicators_concat(self,path,years):

        frames = []
        for items in years:
            temp_data = []
            temp_index = []
            #annual_return max_retreat volatility sharp calmar daily_win_ratio win_lose_ratio
            for k in self.params:

                x = [items,
                self.annual_return('asset'+ str(k),items),
                self.max_draw('asset'+ str(k),items),
                self.volatility('asset'+ str(k),items),
                self.sharp('asset'+ str(k),0.4,items),
                self.calmar('asset'+ str(k),items),
                self.daily_win_ratio('asset'+ str(k),items),
                self.win_lose_ratio('asset'+ str(k),items),
                self.total_turnover('asset'+ str(k),items),
                self.average_daily_turnover('asset'+ str(k),items),
                self.average_daily_position('asset'+ str(k),items),
                self.minor_average_return('asset'+ str(k),items)]
                temp_data.append(x)
                temp_index.append('asset'+ str(k))
            DataFrame = pd.DataFrame(temp_data,index=temp_index,columns=['year','annual_return', 'max_draw', 'volatility', 'sharp','calmar','daily_win_ratio','win_lose_ratio','total_turnover','average_daily_turnover','average_daily_position','minor_average_return'])
            frames.append(DataFrame)
        DataFrame = pd.concat(frames)
        DataFrame.to_csv(path_or_buf=path)

    def plot_figure(self,asset_num,year):
        #待完善：legend
        t1 = time.strptime(self.year_slice[year]['time'].iat[0],"%Y-%m-%d")
        t2 = time.strptime(self.year_slice[year]['time'].iat[-1],"%Y-%m-%d")
        d1 = datetime.datetime(t1.tm_year, t1.tm_mon, t1.tm_mday)
        d2 = datetime.datetime(t1.tm_year, t2.tm_mon, t2.tm_mday)
        plt.figure()
        plt.subplots_adjust(hspace=1, wspace=1)
        plt.subplot(3,1,1)
        self.year_slice[year]['asset'+ str(asset_num)].plot(legend = True)
        self.year_slice[year]['cumulative_return'].plot(x=None, y=None, kind='line', ax=None, subplots=False, sharex=None, sharey=False, layout=None, figsize=None, use_index=True, title=None, grid=None, legend=True, style=None, logx=False, logy=False, loglog=False, xticks=None, yticks=None, xlim=None, ylim=None, rot=None, fontsize=None, colormap=None, table=False, yerr=None, xerr=None, secondary_y=False, sort_columns=False)

        plt.subplot(3,1,2)
        f2 = plt.bar(range(len(self.year_slice[year]['transaction'+ str(asset_num)])), self.year_slice[year]['transaction'+ str(asset_num)].tolist(),tick_label= None,label='transaction'+ str(asset_num))
        plt.legend((f2,),('transaction'+ str(asset_num),))

        plt.subplot(3,1,3)
        f3 = plt.bar(range(len(self.year_slice[year]['pnl'+ str(asset_num)])),self.year_slice[year]['pnl'+ str(asset_num)].tolist(),label='pnl'+ str(asset_num))
        plt.legend((f3,),('pnl'+ str(asset_num),))

        plt.show()

#if __name__=='__main__':
#
#    indicators = Indicators('E:\\Intern\\zxjt\\future_strategy\\total3.csv', [5,10,20])
#    indicators.write_indicators_concat('E:\\Intern\\zxjt\\future_strategy\\write_indicators.csv',['2017','2018'])
#    indicators.plot_figure(10,'2018')