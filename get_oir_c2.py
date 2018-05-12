#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 22 16:26:42 2018

@author: weiss

4.22 
1.增加了近月函数this_contract()
2.调整了部分语法结构适应合约key
3.调整了部分逻辑冗余

4.23
1.修复更新bug

4.30
1.修复近月合约数据缺失

5.7
1.改正近月合约定义

5.8
1.修正合并数据逻辑

5.10
1.修正合并数据部分的代码误删和错误
2.精简和优化部分代码结构

"""


import time as t
import datetime
import pandas as pd
import numpy as np
import os
import warnings
from WindPy import *
w.start()
warnings.filterwarnings("ignore")

class oir(object):

    def __init__(self,homePath, updatebegin = 20100101, endDate = \
                 int(t.strftime('%Y%m%d',t.localtime(t.time()))) ,params = [5,10,20]):
        self.homePath = homePath + '/'
        self.tradeDateList = pd.read_csv(self.homePath +'tradeDateList.csv')
        self.params = params
        self.suffix = '.h5'
        self.beginDate = updatebegin
        self.time =  t.time()
        if t.localtime(self.time).tm_hour < 15:
            self.workDate = int(t.strftime('%Y%m%d',\
                                         t.localtime(self.time - 24 * 60 *60)))
        else:
            self.workDate = int(t.strftime('%Y%m%d',t.localtime(self.time)))
        #确定所需更新的日期
        if endDate < self.workDate:
            self.workDate = endDate
    
    def this_contract(self,windSymbol):
        symbol = windSymbol.split('.')[0]
        def change_spot(y_month):
            weekday = datetime.strptime(y_month+'-01', "%Y-%m-%d").weekday()
            if weekday <= 5:
                return (14 + 5 - weekday)
            else:
                return (14 + 6)
        def this_month(date):
            day = np.int32(str(date)[6:8])
            if day >= change_spot(str(date)[:4]+'-'+str(date)[4:6]):
                month = np.int32(str(date)[4:6])
                if month == 12:
                    return str(np.int32(str(date)[2:4])+1)+'01'
                else:
                    return str(date)[2:4]+"%02d"%(month%12+1)
            else:
                return str(date)[2:6]
        self.tradeDateList[symbol+'_contract'] = \
         self.tradeDateList['tradeDate'].apply(lambda x : symbol+this_month(x))
        self.tradeDateList.to_csv(self.homePath +'tradeDateList.csv', index=None)

    def updateDataFromWind(self,windSymbol):
        symbol = windSymbol.split('.')[0]
        colNames = ['tradeDate','ranks','member_name','long_position',
                    'long_position_increase','short_position',
                    'short_position_increase','volume']
        colNamesFinal = ['tradeDate','ranks','member_name','long_position',
                         'long_position_increase','short_position',
                         'short_position_increase','net_position',
                         'net_position_increase','volume','updatingTime']
        colNamesCon = ['tradeDate','member_name','long_position',
                       'long_position_increase','short_position',
                       'short_position_increase','net_position',
                       'net_position_increase','volume','updatingTime']

        #获取合约数据的函数
        def getFutureoirByDate(beginDate,endDate,windSymbol,windCode,position):
            data = w.wset("futureoir","startdate="+beginDate+";enddate="+
                          endDate+";varity="+windSymbol+";wind_code=" +
                          windCode + ";order_by=" + position +
                          ";ranks=all;field=date,ranks,member_name,long_position,long_position_increase,short_position,short_position_increase,vol")
            if len(data.Data) == 0:
                return pd.DataFrame([])
            dataout = pd.DataFrame()
            try:
                for i in range(len(colNames)):
                    dataout[colNames[i]] = data.Data[i]
            except:
                print(windSymbol + " cannot get data on " + date + ' !')
                return pd.DataFrame([])
            dataout['tradeDate'] = dataout['tradeDate'].astype(str)
            dataout['tradeDate'] = pd.to_datetime(dataout['tradeDate'],\
                   format='%Y-%m-%d',errors='ignore')
            dataout['net_position'] = dataout['long_position'] -\
                                      dataout['short_position']
            dataout['net_position_increase'] = \
                              dataout['long_position_increase'] \
                              - dataout['short_position_increase']
            return dataout

        dateList = pd.DataFrame()
        dateList['tradeDate'] =  self.tradeDateList['tradeDate'].astype(str)
        dateList[symbol+'_contract'] = self.tradeDateList[symbol+'_contract']\
                       +'.'+ windSymbol.split('.')[1]

        for position in ['long','short']:
            endDate = str(self.workDate)
            #如果存在数据，从上次更新日之后更新
            status = 0
            data = pd.DataFrame()

            if os.path.exists(self.homePath + 'rank' + self.suffix):
                try:
                    lastData = pd.read_hdf(self.homePath + 'rank' \
                                  + self.suffix, position +'_'+ windSymbol)
                    if len(lastData) == 0:
                        continue
                    lastDate = str(lastData['tradeDate'].iloc[-1])
                    lastDate = lastDate[0:4] + lastDate[5:7] + lastDate[8:10]
                    beginDate = dateList[dateList['tradeDate'] > lastDate]\
                                ['tradeDate'].iloc[0]
                    beginDate = str(beginDate)
                    if beginDate > endDate:
                        continue
                    print(windSymbol+ '_' +position+ ', begin:' + beginDate +\
                          ',end:' + endDate + ' updating...')
                    data = lastData
                except:
                    status = 1
            #不存在
            else:
                status = 1
            if status == 1:
                beginDate = str(self.beginDate)
                print(windSymbol+ '_' +position+', begin:'+\
                      beginDate+' getting...')
            
            tempDateList = dateList[dateList['tradeDate'] >= beginDate]
            tempDateList = tempDateList[tempDateList['tradeDate'] <=\
                            endDate].reset_index(drop=True)
            for i in range(len(tempDateList)):
                date = tempDateList['tradeDate'][i]
                contract = tempDateList[symbol+'_contract'][i]
                print(date)
                if data.empty:
                    data = getFutureoirByDate(date,date,windSymbol,\
                                              contract,position)
                else:
                    temdata = getFutureoirByDate(date,date,windSymbol,\
                                                 contract,position)
                    data = pd.concat([data,temdata])
                    data = data.reset_index(drop=True)
                data['updatingTime'] = t.strftime('%Y-%m-%d %H:%M:%S')
            data = data[colNamesFinal]
            data.to_hdf(self.homePath + 'rank'+self.suffix, position + '_' +\
                        windSymbol)
        def x_or_y(df):
            c = df.columns
            choise = np.sign((df[c[0]]-df[c[1]]).apply(np.sign)+1/2)
            result = pd.DataFrame()
            result[c[0][:-2]] = (df[c[0]]*(1+choise)+df[c[1]]*(1-choise))/2
            if len(c)>2:
                result[c[2][:-2]] = (df[c[2]]*(1+choise)+df[c[3]]*(1-choise))/2
            return result
        
        #生成连续数据
        print('continous data merging...')
        long_p = pd.read_hdf(self.homePath + 'rank'+self.suffix, \
                             'long_' + windSymbol)
        short_p = pd.read_hdf(self.homePath + 'rank'+self.suffix, \
                              'short_' + windSymbol)
        con_position = pd.merge(long_p.drop(['ranks','updatingTime'],axis = 1)\
                    .fillna(0),short_p.drop(['ranks','updatingTime'],\
                    axis = 1).fillna(0),on=['member_name','tradeDate'],\
                    how = 'outer').fillna(0)
        con_position = con_position.sort_values(\
                by=['tradeDate','long_position_x'],ascending = [True,False])
        con_p = pd.DataFrame(data = [],\
                    index = range(len(con_position)),columns = colNamesCon)
        con_position = con_position.reset_index()
        for z in ['long_position','short_position','net_position']:
            print(z +' merging...')
            p_df = con_position[[z+'_x',z+'_y',z+'_increase_x',z+'_increase_y']]
            con_p[[z,z+'_increase']] = x_or_y(p_df)
        p_df = con_position[['volume_x','volume_y']]
        print('volume merging...')
        con_p['volume'] = x_or_y(p_df)
        
        con_p['tradeDate'] = con_position['tradeDate']
        con_p['member_name'] = con_position['member_name']
        con_p['updatingTime'] =  t.strftime('%Y-%m-%d %H:%M:%S')
        con_p=con_p[colNamesCon]
        con_p.to_hdf(self.homePath  + 'rank'+self.suffix,windSymbol)
        print (symbol + " futureoir source data update complete!")
        return

    def getSignal(self,windSymbol):
        con_position = pd.read_hdf(self.homePath + 'rank'+self.suffix,windSymbol)
        #强制默认参数为[5,10,20]，否则出错
        sum_position = pd.DataFrame(data = [],index = range(len(con_position)),\
                       columns = ['tradeDate']+['long_position_increase_5']+\
                       ['long_position_increase_10']+['long_position_increase_20']+\
                       ['short_position_increase_5']+['short_position_increase_10']+\
                       ['short_position_increase_20'])
        #生成排名数据
        j = 0
        for i in range(len(con_position)):
            if i == 0 or (con_position['tradeDate'][i] != \
                          con_position['tradeDate'][i-1]):
                sum_position['tradeDate'][j] = con_position['tradeDate'][i]
                for tem_i in range(len(self.params)):
                    sum_position['long_position_increase_'+str(self.params[tem_i])][j] = \
                       con_position['long_position_increase'][i+len(self.params)-1-tem_i]
                    sum_position['short_position_increase_'+str(self.params[tem_i])][j] = \
                       con_position['short_position_increase'][i+len(self.params)-1-tem_i]
                j = j + 1
        sum_position = sum_position.iloc[0:j]
        #signal
        signal = pd.DataFrame()
        signal['tradeDate'] = sum_position['tradeDate']
        for k in self.params:
            signal['signal' + str(k)] = (sum_position['long_position_increase_'+str(k)].\
                   apply(np.sign) - sum_position['short_position_increase_'+str(k)].\
                   apply(np.sign))//2
        print(windSymbol.split('.')[0] + ' signal complete !')
        return signal
    
if __name__=='__main__':
    homePath = '/Users/weiss/Downloads'
    windSymbol = 'IF.CFE'
    IF = oir(homePath,updatebegin = 20170101,endDate = 20180328)
    IF.this_contract(windSymbol)
    IF.updateDataFromWind(windSymbol)
    sig = IF.getSignal(windSymbol)
    sig.to_csv(homePath + '/signal.csv',index = None)