# spyder_cta
Spyder_cta is a trading python library.
# Getting Started
将tradeDateList.h5存储在主路径下(唯一必要的初始数据存储文件)

将main.py,get_oir2.py, get_oir.py, asset_curve.py, indicator17.py存储在主路径下
# Initialization
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
# Result
由于wind数据超限，暂时无法提供结果，等数据权限开通后更新
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
- 打印交易记录
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
