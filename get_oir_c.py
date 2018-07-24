#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 22 16:26:42 2018

@author: weiss

2018

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

5.11-5.12
1.增加contract_indic选项(None、'this'、'this&next')，丰富相关逻辑
2.优化代码逻辑结构

5.18
1.增加中金所爬虫函数以及对应信号函数

7.16
1.增加中金所爬虫函数的向后更新功能
2.增加中金所前5、前10的信号，优化输出格式
"""


import time as t
import datetime
import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings("ignore")
try:
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError
except ImportError:
    from urllib2 import urlopen, Request
    from urllib2 import HTTPError
import xml.etree.ElementTree as ET
#from WindPy import *
#w.start()


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
            weekday = datetime.datetime.strptime(y_month+'-01', "%Y-%m-%d").weekday()
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

    def next_contract(self,windSymbol):
        symbol = windSymbol.split('.')[0]
        def _next(contract):
            month = np.int32(contract[-2:])
            if month%3 == 0:
                return '0'
            else:
                return contract[:-2]+"%02d"%(month+(3-month%3))
        self.tradeDateList[symbol+'_next'] = \
         self.tradeDateList[symbol+'_contract'].apply(lambda x : _next(x))
        self.tradeDateList.to_csv(self.homePath +'tradeDateList.csv', index=None)

    def updateDataFromWind(self,windSymbol,contract_indic=None):
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
            if windCode:
                data = w.wset("futureoir","startdate="+beginDate+";enddate="+
                          endDate+";varity="+windSymbol+";wind_code=" +
                          windCode + ";order_by=" + position +
                          ";ranks=all;field=date,ranks,member_name,long_position,long_position_increase,short_position,short_position_increase,vol")
            else:
                data = w.wset("futureoir","startdate="+beginDate+";enddate="+
                          endDate+";varity="+windSymbol+ ";order_by=" + position +
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
        if contract_indic == 'this' or contract_indic == 'this&next':
            self.this_contract(windSymbol)
            dateList[symbol+'_contract'] = self.tradeDateList[symbol+'_contract']\
                       +'.'+ windSymbol.split('.')[1]
        else:
            dateList[symbol+'_contract'] = [None]*len(dateList)

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
        con_p.to_hdf(self.homePath+'rank'+self.suffix,windSymbol)

        if contract_indic == 'this&next':
            self.next_contract(windSymbol)
            dateList[symbol+'_next'] = self.tradeDateList[symbol+'_next']\
                       +'.'+ windSymbol.split('.')[1]
            for position in ['long','short']:
                endDate = str(self.workDate)
                #如果存在数据，从上次更新日之后更新
                status = 0
                data = pd.DataFrame()

                if os.path.exists(self.homePath + 'rank' + self.suffix):
                    try:
                        lastData = pd.read_hdf(self.homePath + 'rank' \
                            + self.suffix, position +'_'+ windSymbol+'_next')
                        if len(lastData) == 0:
                            continue
                        lastDate = str(lastData['tradeDate'].iloc[-1])
                        lastDate = lastDate[0:4] + lastDate[5:7] + lastDate[8:10]
                        beginDate = dateList[dateList['tradeDate'] > lastDate]\
                                ['tradeDate'].iloc[0]
                        beginDate = str(beginDate)
                        if beginDate > endDate:
                            continue
                        print(windSymbol+'_next'+ '_' +position+ ', begin:' +\
                              beginDate +',end:' + endDate + ' updating...')
                        data = lastData
                    except:
                        status = 1
                #不存在
                else:
                    status = 1
                if status == 1:
                    beginDate = str(self.beginDate)
                    print(windSymbol+'_next'+ '_' +position+', begin:'+\
                          beginDate+' getting...')

                tempDateList = dateList[dateList['tradeDate'] >= beginDate]
                tempDateList = tempDateList[tempDateList['tradeDate'] <=\
                                endDate].reset_index(drop=True)
                for i in range(len(tempDateList)):
                    date = tempDateList['tradeDate'][i]
                    contract = tempDateList[symbol+'_next'][i]
                    if len(contract)>6:
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
                        windSymbol+'_next')

            #生成连续数据
            print('continous data merging...')
            long_p = pd.read_hdf(self.homePath + 'rank'+self.suffix, \
                             'long_' + windSymbol+'_next')
            short_p = pd.read_hdf(self.homePath + 'rank'+self.suffix, \
                              'short_' + windSymbol+'_next')
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
                print(z +'_next merging...')
                p_df = con_position[[z+'_x',z+'_y',z+'_increase_x',z+'_increase_y']]
                con_p[[z,z+'_increase']] = x_or_y(p_df)
            p_df = con_position[['volume_x','volume_y']]
            print('volume_next merging...')
            con_p['volume'] = x_or_y(p_df)

            con_p['tradeDate'] = con_position['tradeDate']
            con_p['member_name'] = con_position['member_name']
            con_p['updatingTime'] =  t.strftime('%Y-%m-%d %H:%M:%S')
            con_p=con_p[colNamesCon]
            con_p.to_hdf(self.homePath+'rank'+self.suffix,windSymbol+'_next')

        print (symbol + " futureoir source data update complete!")
        return

    def getSignal(self,windSymbol,contract_indic=None):
        con_position = pd.read_hdf(self.homePath+'rank'+self.suffix,windSymbol)
        #强制默认参数为[5,10,20]，否则出错
        sum_position = pd.DataFrame(data = [],index = range(len(con_position)),\
                       columns = ['tradeDate']+['long_position_increase5']+\
                       ['long_position_increase10']+['long_position_increase20']+\
                       ['short_position_increase5']+['short_position_increase10']+\
                       ['short_position_increase20'])
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

        if contract_indic == 'this&next':
            con_position_next = pd.read_hdf(self.homePath+'rank'+self.suffix,windSymbol+'_next')
            sum_position_next = pd.DataFrame(data = [],index = range(len(con_position_next)),\
                       columns = ['tradeDate']+['long_position_increase5']+\
                       ['long_position_increase10']+['long_position_increase20']+\
                       ['short_position_increase5']+['short_position_increase10']+\
                       ['short_position_increase20'])
            #生成排名数据
            j = 0
            for i in range(len(con_position_next)):
                if i == 0 or (con_position_next['tradeDate'][i] != \
                              con_position_next['tradeDate'][i-1]):
                    sum_position_next['tradeDate'][j] = con_position_next['tradeDate'][i]
                    for tem_i in range(len(self.params)):
                        sum_position_next['long_position_increase_'\
                                          +str(self.params[tem_i])][j] = \
                           con_position_next['long_position_increase']\
                           [i+len(self.params)-1-tem_i]
                        sum_position_next['short_position_increase_'\
                                          +str(self.params[tem_i])][j] = \
                           con_position_next['short_position_increase']\
                           [i+len(self.params)-1-tem_i]
                    j = j + 1
            sum_position_next = sum_position_next.iloc[0:j]

            sum_position = sum_position.merge(sum_position_next,on=['tradeDate'],how='outer')
            for col in ['long_position_increase5','long_position_increase10',
                        'long_position_increase20','short_position_increase5',
                        'short_position_increase10','short_position_increase20']:
                sum_position[col+'_y'].fillna(0,inplace=True)
                sum_position[col] = sum_position[col+'_x']+sum_position[col+'_y']

        #signal
        signal = pd.DataFrame()
        signal['tradeDate'] = sum_position['tradeDate']
        for k in self.params:
            signal['long' + str(k)] = sum_position['long_position_increase_'+str(k)]
            signal['short' + str(k)] = sum_position['short_position_increase_'+str(k)]
            signal['signal' + str(k)] = (sum_position['long_position_increase_'+str(k)].\
                   apply(np.sign) - sum_position['short_position_increase_'+str(k)].\
                   apply(np.sign))//2
        print(windSymbol.split('.')[0] + ' signal complete !')
        return signal

    def get_rank_data(self,date,variety):
        month = str(date)[0:6]
        day = str(date)[6:]
        SIM_HAEDERS = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}
        try:
            xml1 = urlopen(Request('http://www.cffex.com.cn/sj/ccpm/'+month+'/'+day+'/'+variety+'.xml',
                            headers=SIM_HAEDERS)).read().decode('utf-8', 'ignore')
        except HTTPError as reason:
            if reason.code != 404:
                print(404)

        root = ET.fromstring(xml1)

        data_attr = ['instrumentid','tradingday','datatypeid','rank','shortname',
                     'volume','varvolume','partyid','productid']
        data_attr_old = ['instrumentId','tradingDay','dataTypeId','rank','shortname',
                     'volume','varVolume','partyid','productid']
        """
        posi_attr = ['tradingday','instrumentid','volumeamt','varvolumeamt',
                     'buyvolumeamt','buyvarvolumeamt','sellvolumeamt','sellvarvolumeamt',
                     'productid','futurecompany']
        """
        data = []
        for d in root.findall('data'):
            temp = []
            try:
                for attr in data_attr:
                    t = d.find(attr).text
                    temp.append(t)
                data.append(temp)
                #print(temp)
            except:
                for attr in data_attr_old:
                    t = d.find(attr).text
                    temp.append(t)
                data.append(temp)
        vol5 = [0,0,0]
        varvol5 = [0,0,0]
        vol10 = [0,0,0]
        varvol10 = [0,0,0]
        vol = [0,0,0]
        varvol = [0,0,0]
        for x in data:
            if int(x[3])<=10:
                vol10[int(x[2])] +=int(x[5])
                varvol10[int(x[2])] += int(x[6])
                if int(x[3])<=5:
                    vol5[int(x[2])] +=int(x[5])
                    varvol5[int(x[2])] += int(x[6])
            vol[int(x[2])] +=int(x[5])
            varvol[int(x[2])] += int(x[6])
        return (varvol5[1],varvol5[2],varvol10[1],varvol10[2],varvol[1],varvol[2])

    def get_signal_cffex(self,windSymbol):
        symbol = windSymbol.split('.')[0]
        dateList = pd.DataFrame()
        dateList['tradeDate'] =  self.tradeDateList['tradeDate'].astype(str)
        try:
            last_chg = pd.read_csv(self.homePath+symbol+'_chg.csv')
            first_date = last_chg['tradeDate'].iloc[0]
            if first_date > self.beginDate:
                update_idx = 0
                tempDateList = dateList[dateList['tradeDate'] >= str(self.beginDate)]
            else:
                last_date = last_chg['tradeDate'].iloc[-1]
                print('Last date:', last_date)
                tempDateList = dateList[dateList['tradeDate'] > str(last_date)]
                update_idx = 1
        except:
            update_idx = 0
            tempDateList = dateList[dateList['tradeDate'] >= str(self.beginDate)]
        tempDateList = tempDateList[tempDateList['tradeDate'] <=str(self.workDate)]\
                       .reset_index(drop=True)
        L1, L2, L3, S1, S2, S3 = [], [], [], [], [], []
        for date in tempDateList['tradeDate']:
            print(date)
            try:
                l1,s1,l2,s2,l3,s3 = self.get_rank_data(date,symbol)
                L1.append(l1)
                L2.append(l2)
                L3.append(l3)
                S1.append(s1)
                S2.append(s2)
                S3.append(s3)
            except:
                L1.append(0)
                L2.append(0)
                L3.append(0)
                S1.append(0)
                S2.append(0)
                S3.append(0)
        chg_df = pd.DataFrame({'tradeDate':tempDateList['tradeDate'],\
                               'long5':L1,'short5':S1,\
                               'long10':L2,'short10':S2,\
                               'long20':L3,'short20':S3,\
                               })
        if update_idx == 1:
            chg_df = pd.concat([last_chg,chg_df])
        chg_cols = ['tradeDate','long5','long10','long20',\
                    'short5','short10','short20']
        chg_df = chg_df[chg_cols]
        chg_df.to_csv(self.homePath+symbol+'_chg.csv',index = None)
        signal = pd.DataFrame()
        signal_cols = chg_cols+['signal5','signal10','signal20']
        signal['tradeDate'] = chg_df['tradeDate']
        for para in ['5','10','20']:
            signal['long'+para] = chg_df['long'+para]
            signal['short'+para] = chg_df['short'+para]
            signal['signal'+para] = ((chg_df['long'+para].apply(np.sign) - \
                  chg_df['short'+para].apply(np.sign))/2).apply(int)
        return signal[signal_cols]


if __name__=='__main__':
    homePath = '/Users/weiss/Desktop/zxjt'
    windSymbol = 'IF.CFE'
    IF = oir(homePath,updatebegin = 20100416,endDate = 20180715)
    #IF.updateDataFromWind(windSymbol,contract_indic='this&next')
    #sig = IF.getSignal(windSymbol,contract_indic='this&next')
    sig = IF.get_signal_cffex(windSymbol)
    sig.to_csv(homePath + '/signal.csv',index = None)
