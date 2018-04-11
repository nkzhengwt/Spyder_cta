# -*- coding: utf-8 -*-
"""
Created on Mon Apr  9 11:47:47 2018

@author: Wentao
"""

# -*- coding: utf-8 -*-

import time as t
import pandas as pd
import numpy as np
import os
import warnings
import datetime
import h5py
from WindPy import *
w.start()
warnings.filterwarnings("ignore")


class oir(object):

    def __init__(self,homePath, updatebegin = 20100101, endDate = int(t.strftime('%Y%m%d',t.localtime(t.time()))) ,params = []):
        self.homePath = homePath + '\\'
        self.tradeDateList = pd.read_hdf(self.homePath +'tradeDateList.h5','date')
        self.params = params
        self.suffix = '.h5'
        self.beginDate = updatebegin
        self.time =  t.time()
        if t.localtime(self.time).tm_hour < 17:
            self.workDate = int(t.strftime('%Y%m%d',t.localtime(self.time - 24 * 60 *60)))
        else:
            self.workDate = int(t.strftime('%Y%m%d',t.localtime(self.time)))
        #确定所需更新的日期
        if endDate < self.workDate:
            self.workDate = endDate

    def updateDataFromWind(self,windSymbol):
        colNames = ['tradeDate','ranks','member_name','long_position','long_position_increase','short_position','short_position_increase','volume']
        colNamesFinal = ['tradeDate','ranks','member_name','long_position','long_position_increase','short_position','short_position_increase','net_position','net_position_increase','volume','updatingTime']
        colNamesCon = ['tradeDate','member_name','long_position','long_position_increase','short_position','short_position_increase','net_position','net_position_increase','volume','updatingTime']

        #获取品种数据的函数
        def getFutureoirByDate(beginDate,endDate,windSymbol,position):
            data = w.wset("futureoir","startdate="+beginDate+";enddate="+endDate+";varity="+windSymbol+";order_by=" + position + ";ranks=all;field=date,ranks,member_name,long_position,long_position_increase,short_position,short_position_increase,vol")
#            print(data)
            if len(data.Data) == 0:
                return pd.DataFrame([])
            dataout = pd.DataFrame()
            try:
                dataout['tradeDate'] = data.Data[0]
                dataout['ranks'] = data.Data[1]
                dataout['member_name'] = data.Data[2]
                dataout['long_position'] = data.Data[3]
                dataout['long_position_increase'] = data.Data[4]
                dataout['short_position'] = data.Data[5]
                dataout['short_position_increase'] = data.Data[6]
                dataout['volume'] = data.Data[7]
#                print(dataout.head())
            except:
#                print(data)
                print(windSymbol + "cannot get data on " + date + ' !')
                return pd.DataFrame([])
            dataout['tradeDate'] = dataout['tradeDate'].astype(str)
            dataout['tradeDate'] = pd.to_datetime(dataout['tradeDate'], format='%Y-%m-%d',errors='ignore')
            dataout['net_position'] = dataout['long_position'] - dataout['short_position']
            dataout['net_position_increase'] = dataout['long_position_increase'] - dataout['short_position_increase']
#            print(dataout.head())
            return dataout


        dateList = pd.DataFrame()
        dateList['tradeDate'] =  self.tradeDateList['tradeDate'].astype(str)

        for position in ['long','short']:

            endDate = str(self.workDate)
            #如果存在数据，从上次更新日之后更新
            status = 0
            if os.path.exists(self.homePath + 'rank'+self.suffix):
#                f = h5py.File(self.homePath + 'rank'+self.suffix,'r')
                try:
                    lastData = pd.read_hdf(self.homePath + 'rank'+self.suffix, position + windSymbol)
#                    print(lastData)
                    if len(lastData) == 0:
                        continue
                    lastDate = str(lastData['tradeDate'].iloc[-1])
                    lastDate = lastDate[0:4] + lastDate[5:7] + lastDate[8:10]
#                    print(lastDate)
                    beginDate = dateList[dateList['tradeDate'] > lastDate]['tradeDate'].iloc[0]
                    beginDate = str(beginDate)
                    if beginDate > endDate:
                        continue
                    print(windSymbol+ '_' +position+ ', begin:' + beginDate + ',end:' + endDate + ' updating...')
                    tempDateList = dateList[dateList['tradeDate'] >= beginDate]
                    tempDateList = tempDateList[tempDateList['tradeDate'] <= endDate]['tradeDate']
                    data = pd.DataFrame()
                    #每个交易日获取一次数据
                    for date in tempDateList:
                        date = str(date)
                        date = date[0:4] + '-' + date[4:6] + '-' + date[6:8]
#                        print(date)
                        if data.empty:
                            print('new')
                        data = getFutureoirByDate(date,date,windSymbol,position)
                    else:
                        temdata = getFutureoirByDate(date,date,windSymbol,position)
                        data = pd.concat([data,temdata])
                    data['updatingTime'] = t.strftime('%Y-%m-%d %H:%M:%S')
                    data = pd.concat([lastData,data])
                except:
                    status = 1
#                f.close()
            #不存在
            else:
                status = 1
            if status == 1:
                beginDate = str(self.beginDate)
                print(windSymbol+ '_' +position+', begin:'+beginDate+' getting...')
                tempDateList = dateList[dateList['tradeDate'] >= beginDate]
                tempDateList = tempDateList[tempDateList['tradeDate'] <= endDate]['tradeDate']
                data = pd.DataFrame()
                for date in tempDateList:
                    date = str(date)
                    date = date[0:4] + '-' + date[4:6] + '-' + date[6:8]
                    print(date)
                    if data.empty:
                        print('new')
                        data = getFutureoirByDate(date,date,windSymbol,position)
                    else:
                        temdata = getFutureoirByDate(date,date,windSymbol,position)
                        data = pd.concat([data,temdata])
                    data['updatingTime'] = t.strftime('%Y-%m-%d %H:%M:%S')
            data = data[colNamesFinal]
#            print(data.head())
            data.to_hdf(self.homePath + 'rank'+self.suffix, position + windSymbol)
#            print(data['tradeDate'][1])


        def x_or_y(df):
            if df[z+'_x'] != 0:
                return df[z+'_x']
            else:
                return df[z+'_y']

        #生成
        print('continous data merging...')
        long_p = pd.read_hdf(self.homePath + 'rank'+self.suffix, 'long' + windSymbol)
        short_p = pd.read_hdf(self.homePath + 'rank'+self.suffix, 'short' + windSymbol)
        con_position = pd.merge(long_p.drop(['ranks','updatingTime'],axis = 1).fillna(0),short_p.drop(['ranks','updatingTime'],axis = 1).fillna(0),on=['member_name','tradeDate'],how = 'outer').fillna(0)
        con_position = con_position.sort_values(by=['tradeDate','long_position_x'],ascending = [True,False])
        con_p = pd.DataFrame(data = [],index = range(len(con_position)),columns = colNamesCon)
        con_position = con_position.reset_index()
        for z in ['long_position','long_position_increase','short_position','short_position_increase','net_position','net_position_increase','volume']:
            print(z +' merging...')
            con_p[z] = con_position.apply(x_or_y,axis = 1)
        con_p['tradeDate'] = con_position['tradeDate']
        con_p['member_name'] = con_position['member_name']
        con_p['updatingTime'] =  t.strftime('%Y-%m-%d %H:%M:%S')
        con_p=con_p[colNamesCon]
        con_p.to_hdf(self.homePath  + 'rank'+self.suffix,windSymbol)
        print (" futureoir source data update complete!")
        return

    def getSignal(self,windSymbol):
        temparams = [5,10,20]
        temindex = 0
#        con_position = pd.read_csv(self.homePath +'oir' + '\\' + windSymbol + '.csv', encoding='GB2312')
        con_position = pd.read_hdf(self.homePath  + 'rank'+self.suffix,windSymbol)
#        print(con_position.head())
        #con_position = con_position[con_position['tradeDate'] >= str(beginDate)]
        sum_position = pd.DataFrame(data = [],index = range(len(con_position)),columns = ['tradeDate']+['long_position_increase']+['short_position_increase'])
        #print(con_position)
        #生成排名数据
        j = 0
        for i in range(len(con_position)):
            if i == 0 or (con_position['tradeDate'][i] != con_position['tradeDate'][i-1]):
                sum_position['tradeDate'][j] = con_position['tradeDate'][i]
                sum_position['long_position_increase'][j] = con_position['long_position_increase'][i-1+len(temparams)-temindex]
                sum_position['short_position_increase'][j] = con_position['short_position_increase'][i-1+len(temparams)-temindex]
                j = j + 1
        sum_position = sum_position.iloc[0:j]
        #signal
        signal = pd.DataFrame()
        signal['tradeDate'] = sum_position['tradeDate']
        #signal['symbol'] = windSymbol
        for k in self.params:
            signal['signal' + str(k)] = (sum_position['long_position_increase'].apply(np.sign) - sum_position['short_position_increase'].apply(np.sign))//2
        return signal

#
#if __name__=='__main__':
#    homePath = 'E:\\Intern\\zxjt\\future_strategy'
#    params = [5,10,20]
#    IF = oir(homePath,updatebegin = 20180202,endDate = 20180205,params = params)
#    IF.updateDataFromWind('IF.CFE')
#    sig = IF.getSignal('IF.CFE')
#    sig.to_csv(homePath + '\\oir\\signal.csv',index = None)
