# 凭证库使用手册

> 本手册中以 `$Automation` 表示本项目在计算机中的绝对路径

## 项目说明

#### 代码文件

凭证库代码文件分为以下部分：

- 运行文件，`$Automation - runEntryGeneration.py`
- 主体流程，`$Automation - entry_generation`，安排和处理凭证的生成方式和生成顺序
- 时点数据对象，`$Automation - sheets - entry`，持仓、会计余额、凭证对象
- 流水数据对象，`$Automation - sheets - flowing`，推动和影响资产和负债的流水


#### 依赖库

- [pandas](http://pandas.pydata.org/)：快读读取、处理文件和数据库数据
- [sqlalchemy](https://www.sqlalchemy.org/)：sqlite3 本地缓存数据库连接
- [extended](https://github.com/mingotang/ExtendedModules)：数据模板和结构模板
- [Socketer](https://github.com/mingotang/Socketer)：转接wind数据


#### 参数设置

运行参数采用全局通用参数，可以在 `$Automation - settings.yaml` 中设置，其中：

- DataBase：会计数据库登录配置
- Valuation：何梦洁估值表配置（用于数据提取和比对）
- WindSocketServer：wind转接目标地址，用于本机没有wind数据使用权的时候从另一台机器转接
- Log：运行日志输出规则


#### 数据库依赖

- `jm_fundmanagement`：大部分数据来源和数据储存库
- `jiuming_ta_new`：自有产品申赎数据来源


## 运行指南

凭证库的运行和使用遵循 “运行 - 检查出现问题 - 解决问题 - 再次运行” 的逻辑，凭证的生成过程中存在颇多检查，
若存在问题则会抛出运行异常并停止运行，只有在解决问题之后才可以继续顺利运行。


#### 解决运行异常

运行过程中若发生问题停止运行，需要搞清楚两个问题：发生了什么问题？问题在哪里发生？在此以某一次运行时所抛出异常举例。


1 根据报错信息找到发生了什么问题，运行异常如下：


    Exception in thread Thread-1:
    Traceback (most recent call last):
      File "C:\Users\Administrator.SC-201606081350\AppData\Local\Programs\Python\Python37\lib\threading.py", line 917, in _bootstrap_inner
        self.run()
      File "C:\Users\Administrator.SC-201606081350\AppData\Local\Programs\Python\Python37\lib\threading.py", line 865, in run
        self._target(*self._args, **self._kwargs)
      File "C:\Documents\Automation\core\EventEngine.py", line 74, in __run__
        self.__process__(event)
      File "C:\Documents\Automation\core\EventEngine.py", line 84, in __process__
        handler(event)
      File "C:/Documents/Automation/entry_generation/Generator.py", line 932, in __position_update_process__
        self.update_position(data)
      File "C:/Documents/Automation/entry_generation/Generator.py", line 942, in update_position
        pos.update_from(pos_move)
      File "C:\Documents\Automation\sheets\entry\Position.py", line 312, in update_from
        raise RuntimeError(data)
    RuntimeError: EntryPositionMove: {'security_code': '002372.SZ', 'security_name': '伟星新材', 'product': '久铭2号', 'date': datetime.date(2019, 1, 2), 'institution': '中信', 'trade_direction': '卖出', 'offset': '平', 'trade_volume': 10000.0, 'cash_move': nan, 'trade_price': 14.752, 'trade_amount': 147520.0, 'currency': 'RMB'}
    Generator.py 955 DEBUG: generating jounal entry for StockFlowing: product=久铭2号, institution=申万, date=2019-01-02, contract=, capital_account=, shareholder_code=B881048961, security_code=600566.SH, security_name=济川药业, trade_class=证券卖出, trade_price=30.19, trade_amount=60380.0, trade_volume=2000.0, cash_move=60300.3, currency=RMB; 

异常在文件 `C:\Documents\Automation\sheets\entry\Position.py` 中被第312行代码 `raise RuntimeError(data)` 抛出，
该异常是一个因为某些原因自定义的异常，异常发生是源于某些业务中数据不符合处理预期，具体问题则根据 `raise RuntimeError(data)` 之前的代码确定。

2 根据日志信息找到问题发生在哪个业务流程中，日志信息如下：


    Generator.py 955 DEBUG: generating jounal entry for StockFlowing: product=久铭2号, institution=中信, date=2019-01-02, contract=, capital_account=, shareholder_code=0899125999, security_code=002372.SZ, security_name=伟星新材, trade_class=证券卖出, trade_price=14.752, trade_amount=147520.0, trade_volume=10000.0, cash_move=147308.44, currency=RMB; 
    Generator.py 935 DEBUG: position updated by EntryPositionMove: {'security_code': '002372.SZ', 'security_name': '伟星新材', 'product': '久铭2号', 'date': datetime.date(2019, 1, 2), 'institution': '中信', 'trade_direction': '卖出', 'offset': '平', 'trade_volume': 10000.0, 'cash_move': nan, 'trade_price': 14.752, 'trade_amount': 147520.0, 'currency': 'RMB'}

问题发生在根据股票流水生成凭证的过程中（`generating jounal entry for StockFlowing`），事实上，该流水的处理过程中既
需要生成凭证还需要根据流水更新持仓（处理细节见 `$Automation - sheets - flowing - StockFlow.py`），在更新持仓的时候抛出了这个
异常（`update position by EntryPositionMove`）。


#### 解决净资产差异

凭证库运行结束之后会比对估值表净资产数据，若净资产发生差异会在运行日志最后给出差异描述，例如：


    2019-03-21 16:51:27,524 Generator.py run 773:  INFO, =========|=========|==
    2019-03-21 16:51:27,526 Generator.py run 778:  INFO, 稳健6号, 191.91, 2.689070291195701e-06, 预提费用：-7.93, 应交税费：-0.86, 
    2019-03-21 16:51:27,552 Generator.py run 773:  INFO, =========|====
    2019-03-21 16:51:27,553 Generator.py run 778:  INFO, 稳健7号, 29.99, 2.028422839253409e-07, 预提费用：-0.02, 应交税费：-2.66, 
    2019-03-21 16:51:27,593 Generator.py run 773:  INFO, 
    2019-03-21 16:51:27,594 Generator.py run 778:  INFO, 稳健19号, -0.22, -1.9793581733291937e-06, 预提费用：0.0, 应交税费：0.0, 
    2019-03-21 16:51:27,612 Generator.py run 773:  INFO, 
    2019-03-21 16:51:27,613 Generator.py run 778:  INFO, 稳健21号, -0.95, -9.296947234804968e-06, 预提费用：0.0, 应交税费：0.0, 
    2019-03-21 16:51:27,632 Generator.py run 773:  INFO, =========|=========|=========|=
    2019-03-21 16:51:27,633 Generator.py run 778:  INFO, 久铭2号, 1477.06, 3.919288451351274e-06, 预提费用：-0.05, 应交税费：-7.52, 


凭证库给出的运行结果和净资产的差异按照 “绝对值，相对值” 排列，根据给出的差异提示找到差异原因并解决问题或加入未考虑到的因素。
上述例子中，稳健6号和稳健7号的差异来源于估值表在非工作日不计提债券利息而本系统根据平滑原则计提，久铭2号的差异除了债券利息计提之外
还有估值表在非工作日使用了非工作日的基金净值估值而本系统使用的是上一个工作日的公布净值，稳健19号和稳健21号则是小数点误差。


## 架构设计

凭证库对应业务逻辑按照以下顺序执行凭证处理：


|业务|对象|数据来源|备注|
|---|---|---|---|
|管理费计提|ManagementFeePayableFlow|何梦洁估值表|应当是最后一步操作，暂时按照小何数据放在第一步进行|
|业绩报酬计提|ManagementFeePayableFlow|何梦洁估值表|应当是最后一步操作，暂时按照小何数据放在第一步进行|
|管理费返还|ManagementFeeReceivableFlow|何梦洁估值表|应当是最后一步操作，暂时按照小何数据放在第一步进行|
|产品申赎确认|TaConfirmFlow|jiuming_ta_new.申赎流水表|确认其他人（基金）申赎该产品|
|基金投资申赎流水处理|FundConfirmFlow|jiuming_ta_new.申赎流水表，jm_fundmanagement.录入基金交易流水|确认基金投资申赎|
|债券利息计提|BondIntersetsFlow|jm_fundmanagement.会计产品持仓表||
|应收股利计提|DividendInfo|wind和jm_fundmanagement.会计产品持仓表||
|银行流水处理|BankFlowing|jm_fundmanagement.录入银行标准流水||
|存借款利息计提|InterestRate|jm_fundmanagement.会计科目余额表||
|股票流水处理|StockFlowing|jm_fundmanagement.原始普通流水记录||
|期权流水处理|OptionFlowing|jm_fundmanagement.原始期权流水记录||
|期货流水处理|FutureFlowing|jm_fundmanagement.原始期货流水记录||
|债券流水处理|BondFlowing|jm_fundmanagement.原始普通流水记录||
|收益互换结算调整|SwapFlow|jm_fundmanagement.原始收益互换账户资金记录||
|当日证券估值增值处理|DailyValueAddedFlowing|会计产品持仓表|经过流水更新的产品持仓表|
|增值税处理|VATSum|当日证券估值增值结果和交易价差结果||
|自定义调整|ModifyFlowing|jm_fundmanagement.录入调整流水|处理意外情况，如国君期权利息计算没流水等|


其中 `增值税处理` 遵循以下细则：

1. 根据应税规则计算普通账户中的基金交易、和衍生品账户的期货交易和期权交易涉及到的价差收入增值税
2. 根据当日证券估值增值处理过程中每一个应税证券计算其增值部分对应的预提增值税
3. 根据前一日的记录计算截止今日的价差收入增值税总额和预提增值税总额，若
    - 价差总额为正（赚钱），预提总额为正（赚钱）：各自生成今日增加部分增值税凭证
    - 价差总额为正，预提总额为负：生成价差今日增加部分增值税凭证，生成预提增值税归零的凭证
    - 价差总额为负，预提总额为正：生成预提总额抵减价差总额后的预提总额增加部分凭证，生成价差增值税归零的凭证
    - 价差总额为负，预提总额为负：各自生成增值税归零的凭证

