# -*- encoding: UTF-8 -*-
import math

from collections import namedtuple
from jetend import depreciated_method


# ---- [最大精度] ---- #
MAX_DECIMAL = 8

# ---- [预定值] ---- #
EMPTY_STRING = ''
EMPTY_TO_BE_FILLED = ''
EMPTY_FLOAT_RANGE = (None, math.nan,)
EMPTY_STRING_RANGE = (None, '',)

# ---- [交易方向] ---- #
DIRECTION_BUY = '买入'
DIRECTION_SELL = '卖出'
DIRECTION_NONE = '/',

# ---- [交易开平] ---- #
OFFSET_OPEN = '开'
OFFSET_CLOSE = '平'
OFFSET_NONE = 'None'

# ---- [仓位类别（期权）] ---- #
WAREHOUSE_RIGHT = '权利方'
WAREHOUSE_VOLUNTARY = '义务方'
WAREHOUSE_NONE = 'None'

# ---- [现金方向] ---- #
DIRECTION_RECEIVE = '收入'
DIRECTION_PAY = '支出'

# ---- [借贷方向] ---- #
# SIDE_DEBIT_EN = 'debit'
# SIDE_CREDIT_EN = 'credit'
SIDE_DEBIT_CN = '借'
SIDE_CREDIT_CN = '贷'
SIDE_DEBIT_CREDIT = '借贷'

# ---- [证券类型] ---- # security_type
SECURITY_TYPE_BOND = '债券'
SECURITY_TYPE_FUND = '基金'
SECURITY_TYPE_FUTURE = '期货'
SECURITY_TYPE_OPTION = '期权'
SECURITY_TYPE_STOCK = '股票'
SECURITY_TYPE_BOND_INTEREST = '债券利息'
SECURITY_TYPE_ASSET_BUY_BACK = '购入反售'

SECURITY_TYPE_RANGE = {
    SECURITY_TYPE_BOND, SECURITY_TYPE_FUND, SECURITY_TYPE_FUTURE,
    SECURITY_TYPE_OPTION, SECURITY_TYPE_STOCK, SECURITY_TYPE_BOND_INTEREST
}

# ---- [货币记录] ---- #
# CURRENCY_RMB_CN = ''
CURRENCY_RMB_EN = 'RMB'
CURRENCY_USD_EN = 'USD'
CURRENCY_MAP = {
    '人民币': 'RMB', 'RMB': 'RMB',
    'HKD': 'HKD', '港币': 'HKD',
}

# ---- [税率] ---- #
TAX_RATE_VAT = 0.03  # 增值税
TAX_RATE_BT = 0.07  # 城建税
TAX_RATE_ES = 0.03  # 教育费附加
TAX_RATE_LES = 0.02  # 地方教育费附加

# ---- [匹配类型] ---- #
MAP_DISLOCATION = '匹配错位'
MAP_RISK = '匹配存在风险'
MAP_DONE = '匹配完成'

# ---------------------------------------------------------------------- #
ACCOUNT_NAME_CODE_MAP = {
    '银行存款': 1002, '存出保证金': 1031, '结算备付金': 1021,
    '股票投资': 1102, '债券投资': 1103, '基金投资': 1105, '权证投资': 1106, '收益互换': 1107,
    '应收股利': 1203, '应收利息': 1204, '应收申购款': 1207, '其他应收款': 1221,
    '短期借款': 2001,
    '应付赎回款': 2203, '应付管理人报酬': 2206, '应交税费': 2221, '应付利息': 2231, '其他应付款': 2241, '预提费用': 2501,
    '证券清算款': 3003, '实收基金': 4001, '损益平准金': 4011, '利润分配': 4104,
    '利息收入': 6011, '公允价值变动损益': 6101, '投资收益': 6111,
    '管理人报酬': 6403, '交易费用': 6407, '利息支出': 6411, '其他费用': 6605,
    '所得税费用': 6902, '税金及附加': 680201, '预估税金及附加': 680202,
}
# 一级科目
ACCOUNT_NAME_LEVEL_ONE = (
    '实收基金',
)
# 二级科目
ACCOUNT_NAME_LEVEL_TWO = (
    '应收申购款', '应付赎回款', '应付管理人报酬', '损益平准金', '管理人报酬', '预估税金及附加',
)
# 三级科目
ACCOUNT_NAME_LEVEL_THREE = (
    '银行存款', '存出保证金', '应收股利', '收益互换', '结算备付金', 
    '短期借款', '应付利息', '其他应付款', '其他应收款', '公允价值变动损益', '交易费用', '其他费用', '税金及附加', '预提费用',
)
# 四级科目
ACCOUNT_NAME_LEVEL_FOUR = (
    '股票投资', '债券投资', '基金投资', '权证投资',
    '应收利息', '应交税费', '证券清算款',
    '利息收入', '投资收益', '利息支出', '所得税费用',
)

# ---------------------------------------------------------------------- #
CheckResult = namedtuple('CheckResult', ['status', 'text'])


# ---------------------------------------------------------------------- #
class DataBaseName(object):
    """数据库名 Database name of 172"""
    entry = 'jiuming_entry'
    journal = 'jiuming_journal'
    transfer_agent = 'jiuming_ta'
    transfer_agent_fee = 'jiuming_ta_fee'
    transfer_agent_new = 'jiuming_ta_new'
    valuation = 'jiuming_valuation'
    management = 'jm_fundmanagement'


# ---------------------------------------------------------------------- #
def safe_division(upper: float, lower: float, zero_error=0.0):
    if abs(lower) < 0.001:
        return zero_error
    else:
        return upper / lower

def str_similarity(base_string, compare_string):
    count = 0
    for i in range(len(compare_string)):
        if compare_string[i] in base_string:
            count += 1
    if len(base_string) > 0:
        return count / len(base_string)
    else:
        return 0.0


def str_check(obj):
    import decimal
    if obj is None:
        return ''
    elif isinstance(obj, str):
        return obj.strip()
    elif isinstance(obj, float):
        if math.isnan(obj):
            return 'nan'
        if abs(decimal.Decimal(str(obj)).as_tuple().exponent) > MAX_DECIMAL:
            return str(round(obj, MAX_DECIMAL))
        else:
            return str(float(obj))
    else:
        try:
            return str_check(str(obj))
        except ValueError:
            raise NotImplementedError('got str value {} with type {}'.format(obj, type(obj)))


def is_valid_float(obj):
    if isinstance(obj, float):
        return not (math.isnan(obj) or math.isinf(obj))
    elif obj is None:
        return False
    else:
        return is_valid_float(float_check(obj))


def is_valid_str(obj):
    if isinstance(obj, str):
        return obj != ''
    elif obj is None:
        return False
    else:
        return is_valid_str(str_check(obj))


def float_check(obj):
    import decimal
    if obj is None:
        return math.nan
    elif isinstance(obj, str):
        if len(obj) == 0 or obj == 'nan':
            return math.nan
        else:
            return float_check(float(str_check(obj).replace(',', '').replace('HKD', '')))
    elif isinstance(obj, int):
        return float_check(float(obj))
    elif isinstance(obj, float):
        if math.isnan(obj):
            return math.nan
        # if abs(decimal.Decimal(str(obj)).as_tuple().exponent) > MAX_DECIMAL:
        #     return round(obj, MAX_DECIMAL)
        else:
            return obj
    else:
        try:
            return float_check(float(obj))
        except ValueError:
            raise NotImplementedError('got float value {} with type {}'.format(obj, type(obj)))


def is_different_float(f_1: float, f_2: float, gap: float = 0.01):
    if abs(f_1 - f_2) >= gap:
        return True
    else:
        return False


def int_check(obj):
    import math
    if obj is None:
        return None
    elif isinstance(obj, (str, float)):
        obj = float_check(obj)
        if math.isnan(obj):
            return None
        else:
            return int(obj)
    elif isinstance(obj, int):
        return obj
    else:
        try:
            return int_check(int(obj))
        except ValueError:
            raise NotImplementedError('got int value {} with type {}'.format(obj, type(obj)))


def date_check(obj, date_format: str = '%Y-%m-%d'):
    import datetime
    # import pandas as pd
    if obj is None:
        return None
    elif isinstance(obj, str):
        obj = str_check(obj)
        if len(obj) == 0:
            return None
        else:
            return datetime.datetime.strptime(obj, date_format).date()
    elif isinstance(obj, datetime.datetime):
        return obj.date()
    # elif isinstance(obj, pd.datetime):
    #     return datetime.date(obj.year, obj.month, obj.day)
    elif isinstance(obj, datetime.date):
        return obj
    else:
        raise NotImplementedError('got date value {} with type {}'.format(obj, type(obj)))


def datetime_check(obj, datetime_format: str = '%Y-%m-%d %H:%M:%S'):
    import datetime
    import pandas as pd
    if obj is None:
        return None
    elif isinstance(obj, str):
        obj = str_check(obj)
        if obj is None:
            return None
        else:
            try:
                return datetime.datetime.strptime(obj, datetime_format)
            except ValueError as va_error:
                print(obj)
                raise va_error
    elif isinstance(obj, datetime.datetime):
        return obj
    elif isinstance(obj, pd.datetime):
        return datetime.datetime(obj.year, obj.month, obj.day, obj.hour, obj.minute, obj.second, obj.microsecond)
    elif isinstance(obj, datetime.date):
        return datetime.datetime.combine(obj, datetime.time())
    else:
        raise NotImplementedError('got date value {} with type {}'.format(obj, type(obj)))
