# -*- coding: utf-8 -*-
"""
Created on Sun Apr  8 00:23:35 2018

@author: Wentao
"""

#from get_oir2 import *
from get_oir_c import *
from get_quo import *
from indicator17 import *
from assetcurve import *
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

if __name__=='__main__':
    # 设置主路径
    homePath = 'E:\\Intern\\zxjt\\test14'
    # 设置持仓排名参数，代表前n名持仓排名
    params =[20] #参数选择从5,10,20中选择
    # 设置保证金比率
    deposit = 1#0.15
    # 设置佣金比率
    commission = 0.000023#0.000023
    # 设置合约乘数
    multiplier = 300
    # 设置起始日期
    updatebegin = 20100416
    endDate = 20180724
    # 设置合约品种
    windSymbol = 'IF.CFE'
    # 提取信号
    IF = oir(homePath,updatebegin,endDate)
    sig = IF.get_signal_cffex(windSymbol)
    sig.to_hdf('rank.h5','signal'+windSymbol)
#    sig = pd.read_hdf('rank.h5','signal'+windSymbol)
    # 提取或更新合约行情数据
    Ob_quo = Quo(homePath,updatebegin ,endDate)
    quo = Ob_quo.updateDataFromWind(windSymbol)
    quo.to_hdf('quo.h5',windSymbol)
#    quo = pd.read_hdf('quo.h5',windSymbol)
    # 模拟下单，打印交易日志，生成资金曲线
    Ob_asset = assetcurve(sig,quo,params,deposit,commission)
    asset = Ob_asset.get_curve()
    asset.to_hdf('total.h5',windSymbol)
    # 根据资金曲线计算回测指标，记录回测结果，绘图
    indicators = Indicators(asset,params)
    indicators.write_indicators_concat(homePath+'\\write_indicators.csv')
    indicators.plot_figure(params[0])
