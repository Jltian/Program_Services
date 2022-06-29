## JournalLoader


对账单读取




---

### 读取返回结构

#### 普通账户

    dict(
        product: dict(
            account: dict()  # 账户信息
            flow: list(dict(), )  # 流水信息
            position: list(dict(), )  # 持仓信息
        )
    )


#### 两融账户

    dict(
        product: dict(
            account: dict()  # 账户信息
            flow: list(dict(), )  # 流水信息
            position: list(dict(), )  # 持仓信息
            liabilities: list(dict(), )  # 负债信息
        )
    )


#### 收益互换账户
    
    dict(
        product: dict(
            balance_dict: dict()  
            calculation_dict: dict()
            underlying_list: list(dict(), )
        )
        'exchange_rate': float, 
        'loaded_date': date, 
    )


---


### 指令结构
    
    list(
        dict（ Service Type: str #操作类型
              Operation Level: str #操作权限
              Service Domain: str #操作范围
              Data: dict(         
                         product: str #产品名称
                         position: list(dict(), ) #持仓信息
                         account: dict() #账户信息
                         flow: list(dict(), ) #流水信息
                         liabilities: list(dict(), ) #负债信息 
                         )
              )
        )



## utils
将读取的对账单数据放入dict中，再以‘Data'为键放入更高一级的dict中，最终形成result_list

### 通用数据索引

- Service Type:`str`, 操作类型    
- Operation Level:`str`, 操作权限     
- Service Domain:`str`, 操作范围  
- Data:`dict`, 数据内容   
### 对账单数据索引 

- product:`str`, 产品名称   
- flow:`list`, 流水   
- account:`float`, 账户资金 
- position:`list`, 持仓
- liabilities:`list`, 负债 

























### 产品和机构等信息

产品与机构信息被包含在账户资金、账户持仓和账户流水的字典 dict 对象中，并以如下字段索引：

- product: `str`, 产品
- date: `datetime.date`, 日期
- institution: `str`, 机构
- currency: `str`, 账户结算货币


其他信息如下：

- account_type: `str`, 账户类型
- capital_account: `str`, 资金账号
- customer_id: `str`, 客户号


---

### 普通账户

#### 资金信息

账户资金被读取到字典 dict 对象中，并以如下字段索引：

- cash_amount: `float`, 账户资金
- cash_available: `float`, 账户可用余额
- capital_sum: `float`, 资产总额
- market_sum: `float`, 市值总额


#### 流水信息

- trade_class: `str`, 交易类别
- trade_price: `float`, 交易价格
- trade_volume: `float`, 交易数量
- trade_amount: `float`, 交易额
- cash_move: `float`, 实际资金变动

#### 账户持仓



---

### 收益互换账户



- 
