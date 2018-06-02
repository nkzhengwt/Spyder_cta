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
        self.dataframe['cumulative_return'] = dataframe['cumulative_return']#*1000000
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


###年化收益
    def annual_return(self,asset,year):
        R = self.year_slice[year][asset].iat[-1]/self.year_slice[year][asset].iat[0]
        t1 = time.strptime(self.year_slice[year]['time'].iat[0],"%Y-%m-%d")
        t2 = time.strptime(self.year_slice[year]['time'].iat[-1],"%Y-%m-%d")
        d1 = datetime.datetime(t1.tm_year, t1.tm_mon, t1.tm_mday)
        d2 = datetime.datetime(t1.tm_year, t2.tm_mon, t2.tm_mday)
        n = (d2-d1).days
        n = n/244
#        print('The annual return for %s in %s is %f' %(asset,year,math.pow(R, 1/n)-1))
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
        print('The max draw for %s in %s is %f' %(asset,year,abs(min(self.year_slice[year]['retreat']))))
        return abs(min(self.year_slice[year]['retreat']))

###波动率
    def volatility(self,asset,year):
        print('The volatility for %s in %s is %f' %(asset,year,np.std(self.year_slice[year][asset])*math.sqrt(244/len(self.year_slice[year][asset]))))
        return np.std(self.year_slice[year][asset])*math.sqrt(244/len(self.year_slice[year][asset]))

###夏普比率
    def sharp(self, asset,no_risk_R,year):
        print('The Sharp Ratio for %s in %s is %.7f' %(asset,year,(self.annual_return(asset,year)-no_risk_R)/(self.volatility(asset,year)*math.sqrt(244/len(self.year_slice[year][asset]))+1e-10)))
        return (self.annual_return(asset,year)-no_risk_R)/(self.volatility(asset,year)*math.sqrt(244/len(self.year_slice[year][asset]))+1e-10)

###卡玛比率
    def calmar(self,asset,year):
        print('The Calmar Ratio for %s in %s is %f' %(asset,year,self.annual_return(asset,year)/self.max_draw(asset,year)))
        return self.annual_return(asset,year)/self.max_draw(asset,year)

###日胜率
    def daily_win_ratio(self,asset,year):
        #df的条件选择不是self.dataframe[asset][self.dataframe[asset] > 0]而是self.dataframe[self.dataframe[asset] > 0][asset]
        #！！
        pnl = asset.replace('asset','pnl')
        n1 = len(self.year_slice[year][self.year_slice[year][pnl] > 0][pnl])
        n2 = len(self.year_slice[year][pnl])
        print('The daily win ratio for %s in %s is %f' %(asset,year,n1/n2))
        return n1/n2

###日盈亏比
    def win_lose_ratio(self,asset,year):
        self.year_slice[year]['dif'] = self.year_slice[year][asset] - self.year_slice[year][asset].shift(1)
        print('The win lose ratio for %s in %s is %f' %(asset,year,abs(min(self.year_slice[year]['retreat']))))
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
        #print('The worst draw interval for %s in %s is %s %s' %(asset,year,str(t1),str(t2)))
        return t1,t2

###总换手
    def total_turnover(self,asset,year):
        turnover = asset.replace('asset','turnover')
        print('The total turnover for %s in %s is %f' %(asset,year,sum(self.year_slice[year][turnover])))
        return sum(self.year_slice[year][turnover])

###日均换手
    def average_daily_turnover(self,asset,year):
        t1 = time.strptime(self.year_slice[year]['time'].iat[0],"%Y-%m-%d")
        t2 = time.strptime(self.year_slice[year]['time'].iat[-1],"%Y-%m-%d")
        d1 = datetime.datetime(t1.tm_year, t1.tm_mon, t1.tm_mday)
        d2 = datetime.datetime(t1.tm_year, t2.tm_mon, t2.tm_mday)
        n = (d2-d1).days
        print('The average daily turnover for %s in %s is %f' %(asset,year,self.total_turnover(asset,year)/n))
        return self.total_turnover(asset,year)/n

###日均持仓
    def average_daily_position(self,asset,year):
        position = asset.replace('asset','position')
        print('The average daily position for %s in %s is %f' %(asset,year,self.year_slice[year][position].mean()))
        return self.year_slice[year][position].mean()

###次均收益
    def minor_average_return(self,asset,year):
        position = asset.replace('asset','position')
        sum_pos = sum(self.year_slice[year][self.year_slice[year][position]!=0][position])
        num = len(self.year_slice[year][self.year_slice[year][position]!=0][position])
        print('The minor average return for %s in %s is %f' %(asset,year,sum_pos/num))
        return sum_pos/num

    def write_indicators_concat(self,path):
        frames = []
        for items in self.year_slice:
            temp_data = []
            temp_index = []
            for k in self.params:
                x = [items,
                self.annual_return('asset'+ str(k),items),
                self.max_draw('asset'+ str(k),items),
                self.volatility('asset'+ str(k),items),
                self.sharp('asset'+ str(k),0,items),
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

    def plot_figure(self,asset_num):
        t1 = time.strptime(self.dataframe['time'].iat[0],"%Y-%m-%d")
        t2 = time.strptime(self.dataframe['time'].iat[-1],"%Y-%m-%d")
        d1 = datetime.datetime(t1.tm_year, t1.tm_mon, t1.tm_mday)
        d2 = datetime.datetime(t1.tm_year, t2.tm_mon, t2.tm_mday)
        plt.figure()
        plt.subplots_adjust(hspace=1, wspace=1)

        plt.subplot(3,1,1)
        self.dataframe['asset'+ str(asset_num)].plot(legend = True)
        self.dataframe['cumulative_return'].plot(x=None, y=None, kind='line', ax=None, subplots=False, sharex=None, sharey=False, layout=None, figsize=None, use_index=True, title=None, grid=None, legend=True, style=None, logx=False, logy=False, loglog=False, xticks=None, yticks=None, xlim=None, ylim=None, rot=None, fontsize=None, colormap=None, table=False, yerr=None, xerr=None, secondary_y=False, sort_columns=False)

        plt.subplot(3,1,2)
        f2 = plt.bar(range(len(self.dataframe['transaction'+ str(asset_num)])), self.dataframe['transaction'+ str(asset_num)].tolist(),tick_label= None,label='transaction'+ str(asset_num))
        plt.legend((f2,),('transaction'+ str(asset_num),))

        plt.subplot(3,1,3)
        f3 = plt.bar(range(len(self.dataframe['pnl'+ str(asset_num)])),self.dataframe['pnl'+ str(asset_num)].tolist(),label='pnl'+ str(asset_num))
        plt.legend((f3,),('pnl'+ str(asset_num),))

        plt.show()

if __name__=='__main__':
    indicators = Indicators('/Users/zhubaobao/Documents/Quant/ZXJT/total3.csv', [5,10,20])
    #indicators.write_indicators_concat('/Users/zhubaobao/Documents/Quant/ZXJT/write_indicators.csv')
    indicators.plot_figure(10)
