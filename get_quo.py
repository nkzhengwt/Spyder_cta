# -*- coding: utf-8 -*-
"""
Created on Sat Apr  7 21:10:31 2018

@author: Wentao
"""
import time as t
import pandas as pd
import numpy as np
import os
import warnings
import datetime
from WindPy import *
w.start()
warnings.filterwarnings("ignore")
#df = pd.read_csv('E:\\Intern\\zxjt\\future_strategy\\IF.csv')#,parse_dates=True)
#a=pd.DataFrame({1:[1,1],2:[2,2]})
#a.to_csv('1.csv')
class Quo():
    def __init__(self, homePath, updatebegin = 20100101, endDate = int(t.strftime('%Y%m%d',t.localtime(t.time()))) ):#,params = []):
        self.homePath = homePath + '\\'
        #self.params = params
        self.suffix = '.h5'
        self.beginDate = updatebegin
        self.endDate = endDate
        self.time = t.time()
        if t.localtime(self.time).tm_hour < 17:
            self.workDate = int(t.strftime('%Y%m%d',t.localtime(self.time - 24 * 60 *60)))
        else:
            self.workDate = int(t.strftime('%Y%m%d',t.localtime(self.time)))
        #self.dataframe = dataframe
        #self.series = dataframe['return'].tolist()
    #    self.time = dataframe['time']

    def updateDataFromWind(self,windSymbol):

        #colNamesFinal = ['date','open','high','low','close','volume','settle','vwap','updatingTime']
        #按日获取品种数据的函数
        beginDate = str(self.beginDate)
        endDate = str(self.endDate)
#        print(type(beginDate))
#        print(type(endDate))
        def getFuturequoByDate(beginDate,endDate,windSymbol):
            data = w.wsd(windSymbol, "open,high,low,close,volume,settle,vwap", \
                         beginDate, endDate, "PriceAdj=F")
            #print(data)
            #print(data.Data)
            if len(data.Data) == 0:
                return pd.DataFrame([])
            dataout = pd.DataFrame()
            try:
                dataout['date'] = data.Times
                dataout['open'] = data.Data[0]
                dataout['high'] = data.Data[1]
                dataout['low'] = data.Data[2]
                dataout['close'] = data.Data[3]
                dataout['volume'] = data.Data[4]
                dataout['settle'] = data.Data[5]
                dataout['vwap'] = data.Data[6]
#                print(dataout)
#                print('11111')
            except:
#                print(data)
                print(windSymbol + " cannot get data " +'!')
                return pd.DataFrame([])
            return dataout
        if os.path.exists(self.homePath + '\\' + 'quo' + self.suffix):
            try:
                lastData = pd.read_hdf(self.homePath +  '\\' + \
                                       'quo' + self.suffix,windSymbol)
                lastDate = str(lastData['date'].iloc[-1])
                lastDate = lastDate[0:4] + lastDate[5:7] + lastDate[8:10]
                data = pd.DataFrame()
                print('lastDate: '+lastDate)
                if endDate > lastDate:
    #                if lastDate == beginDate:
    #                    beginDate = str(int(beginDate)+1)
                    print('new')
                    data = getFuturequoByDate(max(str(int(lastDate)+1),beginDate), \
                                              endDate,windSymbol)
                    data = pd.concat([lastData,data],ignore_index=True)
                    data['updatingTime'] = t.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    print('endDate <= lastDate')
                    data= lastData
            except:
                data = getFuturequoByDate(beginDate,endDate,windSymbol)

        else:
            #beginDate = str(self.beginDate)
            data = getFuturequoByDate(beginDate,endDate,windSymbol)

        return data

if __name__=='__main__':
    homePath = 'E:\\Intern\\zxjt\\test'
#    a = pd.DataFrame()
    IF = Quo(homePath,updatebegin = 20180301,endDate = 20180309)
    Quo = IF.updateDataFromWind('IH.CFE')

