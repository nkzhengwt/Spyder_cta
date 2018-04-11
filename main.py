# -*- coding: utf-8 -*-
"""
Created on Sun Apr  8 00:23:35 2018

@author: Wentao
"""

from get_oir2 import *
from get_quo import *
from indicator17 import *
from assetcurve import *
import pandas as pd

if __name__=='__main__':
    homePath = 'E:\\Intern\\zxjt\\test2'
    # 设置持仓排名参数，分别代表前n名持仓排名
    params = [5,10,20]
    # 设置保证金比率
    deposit = 0.15
    # 设置佣金比率
    commission = 0.000023
    # 设置合约乘数
    multiplier = 300
    # 设置起始日期
    updatebegin = 20100101
    endDate = 20180408
    # 设置合约品种
    windSymbol = 'IF.CFE'
    # 提取或更新持仓排名数据
    Ob_oir = oir(homePath,updatebegin ,endDate ,params = params)
    Ob_oir.updateDataFromWind(windSymbol)
    # 提取信号
    sig = Ob_oir.getSignal(windSymbol)
#    sig.to_hdf('rank.h5','signal'+windSymbol)
    # 提取或更新合约行情数据
    Ob_quo = Quo(homePath,updatebegin ,endDate)
    quo = Ob_quo.updateDataFromWind(windSymbol)
    quo.to_hdf('quo.h5',windSymbol)
    # 模拟下单，打印交易日志，生成资金曲线
    Ob_asset = assetcurve(sig,quo,params,deposit,commission)
    asset = Ob_asset.get_curve()
#    asset.to_hdf('total.h5',windSymbol)
    # 根据资金曲线计算回测指标，记录回测结果，绘图
    indicators = Indicators(asset,params)
    indicators.write_indicators_concat(homePath+'\\write_indicators.csv',['2010','2011','2012','2013','2014','2015','2016','2017','2018'])
    indicators.plot_figure(5,'2018')