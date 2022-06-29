# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
from jetend.DataCheck import *


TRADE_DIRECTION_BUY = '买入'
TRADE_DIRECTION_SELL = '卖出'

OFFSET_OPEN = '开'
OFFSET_CLOSE = '平'


PRODUCT_NAME_RANGE = (
    '久铭1号', '久铭2号', '久铭3号', '久铭5号', '久铭6号', '久铭7号', '久铭8号', '久铭9号', '久铭10号',
    '久铭300指数', '全球1号', '久铭50指数', '收益1号', '收益2号', '双盈1号', '稳利2号', '久铭500指数', '久盈2号',
    '稳健1号', '稳健2号', '稳健3号', '稳健5号', '稳健6号', '稳健7号', '稳健8号', '稳健9号',
    '稳健10号', '稳健11号', '稳健12号', '稳健15号', '稳健16号', '稳健17号', '稳健18号', '稳健19号',
    '稳健21号', '稳健22号', '稳健23号', '稳健31号', '稳健32号', '稳健33号',
    '创新稳健1号', '创新稳禄1号', '创新稳健2号',
)


CURRENCY_RANGE_MAP = {
    'RMB': 'RMB', '人民币': 'RMB',
    'USD': 'USD', '美元': 'USD',
    'HKD': 'HKD', '港币': 'HKD',
}


# ================================ [BASIC] ================================ #
def check_str_element(obj: dict, key_tag: str, info: str = ''):
    ele_str = str_check(obj.get(key_tag, None))
    assert is_valid_str(ele_str), '{}信息缺失 {} {}'.format(info, key_tag, obj)
    obj[key_tag] = ele_str.strip()
    return ele_str.strip()


def check_float_element(obj: dict, key_tag: str, info: str = ''):
    ele_float = float_check(obj.get(key_tag, None))
    assert is_valid_float(ele_float), '{}缺失 {} {}'.format(info, key_tag, obj)
    obj[key_tag] = ele_float
    return ele_float


def check_basic_info(obj: dict):
    from datetime import date as datetime_date
    product = check_str_element(obj, 'product', '产品')
    # if '久铭' in product and '创新' in product:
    #     product = product.replace('久铭', '')
    assert product in PRODUCT_NAME_RANGE, str(obj)
    date = obj.get('date')
    assert isinstance(date, datetime_date), str(obj)
    check_str_element(obj, 'institution', '机构')
    currency = check_str_element(obj, 'currency', '账户结算币种')
    obj['currency'] = CURRENCY_RANGE_MAP[currency]


def check_security_info(secu_obj: dict):
    account_type = check_str_element(secu_obj, 'account_type', '账户类型')
    security_code = check_str_element(secu_obj, 'security_code', '证券代码')
    if '港股通' in secu_obj['institution']:
        while len(security_code) < 4:
            security_code = ''.join(['0', security_code])
    if '普通账户' in account_type or '两融账户' in account_type:
        if '.' not in security_code:
            if len(security_code) == 6:
                if security_code[0] in ('6', '5', '3', '7'):
                    secu_obj['security_code'] = '.'.join([security_code, 'SH'])
                elif security_code[0] in ('0', ):
                    secu_obj['security_code'] = '.'.join([security_code, 'SZ'])
                else:
                    raise NotImplementedError(secu_obj)
            elif len(security_code) == 5:
                if security_code[0] in ('0', ):
                    secu_obj['security_code'] = '.'.join([security_code[1:], 'SH'])
                else:
                    raise NotImplementedError(secu_obj)
            elif len(security_code) == 4:
                if security_code[0] in ('0', ):
                    secu_obj['security_code'] = '.'.join([security_code[1:], 'HK'])
                else:
                    raise NotImplementedError(secu_obj)
            else:
                raise NotImplementedError('{}\n{}'.format(security_code, secu_obj))
    elif account_type == '收益互换':
        assert '.' in security_code, str(secu_obj)
    elif '期货账户' in account_type:
        if '.' not in security_code:
            if security_code.upper()[:2] in ('IF', 'IC', 'IH', ):
                secu_obj['security_code'] = '.'.join([security_code, 'CFE'])
            else:
                raise NotImplementedError(secu_obj)
        else:
            raise NotImplementedError(secu_obj)
    else:
        raise NotImplementedError(secu_obj)

    if '普通账户' in account_type or account_type in ('收益互换', ):
        check_str_element(secu_obj, 'security_name', '证券名称').strip()
    elif '两融账户' in account_type:
        pass
    elif '期货账户' in account_type:
        pass
    else:
        raise NotImplementedError(secu_obj)


def check_basic_trade_info(trade_obj: dict):
    check_str_element(trade_obj, 'trade_class', '交易类别')
    check_str_element(trade_obj, 'trade_name', '业务名称')
    trade_direction = check_str_element(trade_obj, 'trade_direction', '交易方向')
    assert trade_direction in (TRADE_DIRECTION_BUY, TRADE_DIRECTION_SELL), trade_direction
    trade_price = check_float_element(trade_obj, 'trade_price', '交易价格')
    trade_volume = check_float_element(trade_obj, 'trade_volume', '交易数量')
    trade_amount = check_float_element(trade_obj, 'trade_amount', '交易额')
    # try:
    #     trade_amount = check_float_element(trade_obj, 'trade_amount', '交易额')
    # except AssertionError:
    #     trade_amount = trade_price * trade_volume
    #     trade_obj['trade_amount'] = trade_amount
    # check_float_element(trade_obj, 'cash_move', '资金变动数量')
    assert check_multiply_match(trade_price, trade_volume, trade_amount, error_percent=0.05), str(trade_obj)


def check_future_trade_info(trade_obj: dict):
    check_str_element(trade_obj, 'trade_class', '交易类别')
    check_str_element(trade_obj, 'trade_name', '业务名称')
    trade_direction = check_str_element(trade_obj, 'trade_direction', '交易方向')
    assert trade_direction in (TRADE_DIRECTION_BUY, TRADE_DIRECTION_SELL), trade_direction
    trade_price = check_float_element(trade_obj, 'trade_price', '交易价格')
    trade_volume = check_float_element(trade_obj, 'trade_volume', '交易数量')


def confirm_normal_trade_flow_list(flow_list: list):
    """检查普通流水要素"""
    for flow in flow_list:
        check_basic_info(flow)
        check_security_info(flow)
        check_basic_trade_info(flow)


def confirm_future_trade_flow_list(flow_list: list):
    """检查期货流水要素"""
    for flow in flow_list:
        check_basic_info(flow)
        check_security_info(flow)
        check_future_trade_info(flow)
