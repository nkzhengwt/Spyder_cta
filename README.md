# Spyder_cta
Spyder_cta is a program that automatically builds spyder trading strategies and backtest it based on the Wind data. Also you can modify it for your trading strategies.
# Install
Spyder_cta is developed with Python 3.
You can use pip to install or upgrade packages below.
```
pip install numpy
pip install pandas
pip install math
pip install os
pip install warnings
pip install datetime
pip install time
pip install matplotlib
```
Also you need to install Wind to get the quote and signal data from it and get WindPy ready to work.
# Getting Started
1. 将tradeDateList.h5存储在主路径下(唯一必要的初始数据存储文件)

2. 将main.py,get_oir2.py, get_oir.py, asset_curve.py, indicator17.py存储在主路径下
3. 初始化参数
4. 运行main.py
# Initialization
You can initialize spyder_cta in main.py.
```
#设置主路径
homePath = 'E:\\test2'
#设置持仓排名参数，分别代表前n名持仓排名
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
```
# Process
![](https://github.com/nkuzhengwt/Spyder_cta/blob/master/process.png)
![](https://github.com/nkuzhengwt/Spyder_cta/blob/master/process2.png)
# Result
20180602更新

![](https://github.com/nkuzhengwt/Spyder_cta/blob/New/result.png)

详细回测指标见：write_indicators.csv

交易记录见：total.h5
# Main Features
## 综合
- 事件驱动 √
- Futures模式 √
- Stock模式 ×
- Forex模式 ×
- 多品种回测 √
- 多参数回测 √
- 多策略回测 x
- 设置手续费，保证金 ✓
- 打印交易日志 √
- plot画图模块 √
- 参数优化模块 ×
## 数据来源
- WIND接口 √
- Tushare接口 ×
## 模拟交易
- 固定资产比 √
- 固定交易手数 ×
- 固定交易资金 ×
- 止盈止损 ×
## 交易日志
- 保证金 √
- 仓位手数及方向 √
- 交易资金额 √
- 当日盈亏 √
- 手续费 √
- 当日换手 √
- 保证金占比 √
- 打印交易记录 √
## 统计分析
- 年化收益 √
- 最大回撤 √
- 波动率 √
- 夏普比率 √
- 卡玛比率 √
- 日胜率 √
- 日盈亏比 √
- 最大回撤区间 √
- 总换手 √
- 日均持仓 √
- 日均换手 √
- 日均持仓 √
- 次均收益 √
- 结合Benchmark分析 ×
# 后记
存在细节之处有待完善
