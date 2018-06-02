# -*- coding: utf-8 -*-
"""
Created on Sun Apr  8 09:30:05 2018

@author: Wentao
"""

import pandas as pd

# 构造下单逻辑及资金净值变化描述
# signal:发生信号序列
# quo:行情数据
# params:信号参数
# deposit:保证金率
# commission: 手续费率
# multipilier:合约乘数
class assetcurve(object):
    def __init__(self,signal,quo,params,deposit,commission = 0,multiplier = 300):
        quo['date'] = quo['date'].astype(str)
        quo['date'] = pd.to_datetime(quo['date'], format='%Y-%m-%dT%H:%M:%S',errors='ignore')
        self.quo = quo
        self.deposit = deposit
        self.commission = commission
        self.multi = multiplier
        self.params = params
        signal['tradeDate'] = pd.to_datetime(signal['tradeDate'],format='%Y%m%d')
        self.signal = signal
        self.total = pd.merge(self.signal, self.quo, how='inner', on=None, \
                         left_on='tradeDate', right_on='date')
        self.total['tradeDate'] = self.total['tradeDate'].astype(str)
        self.total['date'] = self.total['date'].astype(str)
        for i in self.params:
            self.total['asset'+str(i)] = 1
            self.total['transaction'+str(i)] = 0
            self.total['pnl'+str(i)] = 0
            self.total['commission'+str(i)] = 0
            self.total['turnover'+str(i)] = 0
            self.total['position'+str(i)] = 0
            self.total['deposit'+str(i)] = self.deposit
#            self.total['commssion'] = 0
    # 计算最长连续信号持仓周期
    def find_maxsiganlduration(self,signal):
        num = pd.Series()
        for k in self.params:
            temp_arra = []
            temp = 1
            for index in self.total['signal'+str(k)].index[0:-1]:
                if (self.total['signal'+str(k)][index] == signal) & \
                (self.total['signal'+str(k)][index+1] == signal):
                    temp += 1
#                    print(temp)
#                    print(index)
                else:
                    temp_arra.append(temp)
                    temp = 1
            if temp_arra != []:
                num[str(k)] = max(temp_arra)
            else:
                num[str(k)] = 0
        return num
#            print('k:'+str(num[str(k)]))


    def order_buy(self,i,k,num,signal = 1):
        # 第一天买入开仓加杠杆，扣除手续费
        self.total.loc[i+1,['asset'+str(k)]] = \
        self.total['asset'+str(k)][i]*(1 - 1/self.deposit*self.commission)
        # 成交记录
        comm = \
        self.total['asset'+str(k)][i]/self.deposit*self.commission
        self.total.loc[i+1,['commission'+str(k)]] = comm
        tran = \
        + self.total['asset'+str(k)][i+1]/self.deposit
        if self.total['transaction'+str(k)][i+1] == 0:
            self.total.loc[i+1,['transaction'+str(k)]] = tran
        else:
            temp1 = self.total['transaction'+str(k)][i+1]
            self.total.loc[i+1,['transaction'+str(k)]] = temp1 + tran
        turn = abs(tran)/self.total['open'][i+1]/self.multi
        if self.total['turnover'+str(k)][i+1] == 0:
            self.total.loc[i+1,['turnover'+str(k)]] = turn
        else:
            temp2 = self.total['turnover'+str(k)][i+1]
            self.total.loc[i+1,['turnover'+str(k)]] = temp2 + turn
        if self.total['position'+str(k)][i+1] == 0:
            self.total.loc[i+1,['position'+str(k)]] = + turn
        else:
            temp3 = self.total['position'+str(k)][i+1]
            self.total.loc[i+1,['position'+str(k)]] = temp3 +turn
        print('------------信号产生-----------')
        print('建仓日期：'+ self.total['tradeDate'][i+1])
        print('多头开仓：' + str(tran))
        print('手续费:' + str(comm))
        print('成交手数：' + str(turn))
        # 第2天-第num天继续持仓
        for y in range(num-1):
            self.total.loc[i+2+y,['asset'+str(k)]] = \
            self.total['asset'+str(k)][i+1+y]*(1+(self.total['open'][i+2+y] \
            -self.total['open'][i+1+y])/self.total['open'][i+1+y] \
            /self.deposit)
            self.total.loc[i+2+y,['position'+str(k)]] = \
            self.total['position'+str(k)][i+1+y]
            #print(y)
        # 第(num+1)天卖出平仓加杠杆，扣除手续费
        self.total.loc[i+1+num,['asset'+str(k)]] = \
        self.total['asset'+str(k)][i+1]*(1+(self.total['open'][i+1+num] \
        -self.total['open'][i+1])/self.total['open'][i+1] \
        /self.deposit)
        # 成交记录
        tran2 = - self.total['asset'+str(k)][i+1]*self.total['open'][i+1+num] \
        /self.total['open'][i+1]/self.deposit
        self.total.loc[i+1+num,['transaction'+str(k)]] = tran2
        temp = self.total['asset'+str(k)][i+1+num]
        self.total.loc[i+1+num,['asset'+str(k)]] = temp - \
        self.total['asset'+str(k)][i+1]*self.total['open'][i+1+num] \
        /self.total['open'][i+1]/self.deposit*self.commission
        comm2 = self.total['asset'+str(k)][i+1]*self.total['open'][i+1+num] \
        /self.total['open'][i+1]/self.deposit*self.commission
        self.total.loc[i+1+num,['commission'+str(k)]]= comm2
        turn2 = abs(self.total['transaction'+str(k)][i+1+num])/self.total['open'][i+1+num]/self.multi
        self.total.loc[i+1+num,['turnover'+str(k)]] = turn2
        print('平仓日期：'+ self.total['tradeDate'][i+1+num])
        print('多头平仓：' + str(tran2))
        print('手续费:' + str(comm2))
        print('成交手数：' + str(turn2))
        # 记录多日盈亏
        for x in range(num+1):
            self.total.loc[i+1+x,['pnl'+str(k)]] = self.total['asset'+str(k)][i+1+x] \
            -self.total['asset'+str(k)][i+x]
    def order_sell(self,i,k,num,signal = 1):
        # 第一天卖出开仓加杠杆，扣除手续费
        self.total.loc[i+1,['asset'+str(k)]] = \
        self.total['asset'+str(k)][i]*(1 - 1/self.deposit*self.commission)
        # 成交记录
        comm = self.total['asset'+str(k)][i]/self.deposit*self.commission
        self.total.loc[i+1,['commission'+str(k)]] = comm
        tran = \
         - self.total['asset'+str(k)][i+1]/self.deposit
        if self.total['transaction'+str(k)][i+1] == 0:
            self.total.loc[i+1,['transaction'+str(k)]] = tran
        else:
            temp1 = self.total['transaction'+str(k)][i+1]
            self.total.loc[i+1,['transaction'+str(k)]] = temp1 + tran
        turn = abs(tran)/self.total['open'][i+1]/self.multi
        if self.total['turnover'+str(k)][i+1] == 0:
            self.total.loc[i+1,['turnover'+str(k)]] = turn
        else:
            temp2 = self.total['turnover'+str(k)][i+1]
            self.total.loc[i+1,['turnover'+str(k)]] = temp2 + turn
        if self.total['position'+str(k)][i+1] == 0:
            self.total.loc[i+1,['position'+str(k)]] = - turn
        else:
            temp3 = self.total['position'+str(k)][i+1]
            self.total.loc[i+1,['position'+str(k)]] = temp3  - turn
        print('------------信号产生-----------')
        print('建仓日期：'+ self.total['tradeDate'][i+1])
        print('空头开仓：' + str(tran))
        print('手续费:' + str(comm))
        print('成交手数：' + str(turn))
        # 第2天-第num天继续持仓
        for y in range(num-1):
            self.total.loc[i+2+y,['asset'+str(k)]] = \
            self.total['asset'+str(k)][i+1+y]*(1+(self.total['open'][i+1+y] \
            -self.total['open'][i+2+y])/self.total['open'][i+2+y] \
            /self.deposit)
            self.total.loc[i+2+y,['position'+str(k)]] = \
            self.total['position'+str(k)][i+1+y]
        # 第(num+1)天买入平仓加杠杆，扣除手续费
        self.total.loc[i+1+num,['asset'+str(k)]] = \
        self.total['asset'+str(k)][i+1]*(1+(self.total['open'][i+1] \
        -self.total['open'][i+1+num])/self.total['open'][i+1+num] \
        /self.deposit)
        # 成交记录
        tran2 = + self.total['asset'+str(k)][i+1]*self.total['open'][i+1+num] \
        /self.total['open'][i+1]/self.deposit
        self.total.loc[i+1+num,['transaction'+str(k)]] = tran2
        temp = self.total['asset'+str(k)][i+1+num]
        self.total.loc[i+1+num,['asset'+str(k)]] = temp - \
        self.total['asset'+str(k)][i+1]*self.total['open'][i+1] \
        /self.total['open'][i+1+num]/self.deposit*self.commission
        comm2 = self.total['asset'+str(k)][i+1]*self.total['open'][i+1] \
        /self.total['open'][i+1+num]/self.deposit*self.commission
        self.total.loc[i+1+num,['commission'+str(k)]]= comm2
        turn2 =abs(self.total['transaction'+str(k)][i+1+num])/self.total['open'][i+1+num]/self.multi
        self.total.loc[i+1+num,['turnover'+str(k)]] = turn2
        print('平仓日期：'+ self.total['tradeDate'][i+1+num])
        print('空头平仓：' + str(tran2))
        print('手续费:' + str(comm2))
        print('成交手数：' + str(turn2))
        # 记录多日盈亏
        for x in range(num+1):
            self.total.loc[i+1+x,['pnl'+str(k)]] = self.total['asset'+str(k)][i+1+x] \
            -self.total['asset'+str(k)][i+x]
    # 下单逻辑构造
    def get_curve(self):
        # allin:固定资金比
        # fixedamount:固定资金额
        # fixedhand:固定合约手数
        mode = ['allin','fixedamount','fixedhand']
#        self.find_maxsiganlduration(1)
        for j in mode:
            if j == 'allin':
                num_buy = self.find_maxsiganlduration(1)
                num_sell = self.find_maxsiganlduration(-1)
                for k in self.params:
                    # 按日期循环下单
#                    print(num_buy)
                    n = num_buy[str(k)]
                    m = num_sell[str(k)]
                    for i in self.total.index[0:-2]:
                        # 判断做多信号
                        if (self.total['signal'+str(k)][i] == 1):
                            try:
                                # 判断前n天信号是否为连续
                                status = 0
                                for l in range(n-1):
                                    if (list(self.total['signal'+str(k)][(i-1-l):i]) \
                                                       == [1]*(l+1)):
                                        status = 1
                                        break
                                if status == 1:
                                    continue
                                # 判断后n天是否为连续
                                for l in range(n-1)[::-1]:
                                    if (list(self.total['signal'+str(k)][i:(i+2+l)]) \
                                                       == [1]*(l+2)):
                                        self.order_buy(i,k,l+2)
                                        break
                                if (self.total['signal'+str(k)][i+1] != 1):
                                    self.order_buy(i,k,1)
                            except:
                                for l in range(n-1)[::-1]:
                                    if (list(self.total['signal'+str(k)][i:(i+2+l)]) \
                                                       == [1]*(l+2)):
                                        self.order_buy(i,k,l+2)
                                        break
                                if (self.total['signal'+str(k)][i+1] != 1):
                                    self.order_buy(i,k,1)
                        # 判断做空信号
                        elif (self.total['signal'+str(k)][i] == -1):
                            try:
                                status = 0
                                for l in range(m-1):
                                    if (list(self.total['signal'+str(k)][(i-1-l):i]) \
                                                       == [-1]*(l+1)):
                                        status = 1
                                        break
                                if status == 1:
                                    continue
                                # 判断后n天是否为连续
                                for l in range(m-1)[::-1]:
                                    if (list(self.total['signal'+str(k)][i:(i+2+l)]) \
                                                       == [-1]*(l+2)):
                                        self.order_sell(i,k,l+2)
                                        break
                                if (self.total['signal'+str(k)][i+1] != -1):
                                    self.order_sell(i,k,1)
                            except:
                                for l in range(m-1)[::-1]:
                                    if (list(self.total['signal'+str(k)][i:(i+2+l)]) \
                                                       == [-1]*(l+2)):
                                        self.order_sell(i,k,l+2)
                                        break
                                if (self.total['signal'+str(k)][i+1] != -1):
                                    self.order_sell(i,k,1)
                        # 信号未发生，空仓
                        elif self.total['signal'+str(k)][i] == 0:
                            self.total.loc[i+2,['asset'+str(k)]] = self.total['asset'+str(k)][i+1]
        return self.total

#if __name__=='__main__':
#    homePath = 'E:\\Intern\\zxjt\\future_strategy'
#    windSymbol = 'IF.CFE'
#    params = [5,10,20]
#    deposit = 0.15
#    commission = 0.000023
#    multiplier = 300
#    sig = pd.read_csv(homePath + '\\oir\\signal.csv')
#    quo = pd.read_csv(homePath + '\\oir_quo' + '\\' +  windSymbol+'.csv')
#    asset = assetcurve(sig,quo,params,deposit,commission,multiplier)
#    a = asset.get_curve()
#    a.to_hdf('total3.h5','b')

