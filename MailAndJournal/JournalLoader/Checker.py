# -*- encoding: UTF-8 -*-
import re

from jetend.DataCheck import *
from Limits import *


# ================================ [BASIC] ================================ #
def check_str_element(obj: dict, key_tag: str, info: str = '', blank_skip: bool = False):
    ele_str = str_check(obj.get(key_tag, None))
    if blank_skip is False:
        assert is_valid_str(ele_str), '{}信息缺失 {} {}'.format(info, key_tag, obj)
    obj[key_tag] = ele_str.strip()
    return ele_str.strip()


def check_float_element(obj: dict, key_tag: str, info: str = '', blank_skip: bool = False):
    ele_float = float_check(obj.get(key_tag, None))
    if blank_skip is False:
        assert is_valid_float(ele_float), '{}缺失 {} {}'.format(info, key_tag, obj)
    obj[key_tag] = ele_float
    return ele_float


def check_basic_info(obj: dict):
    from datetime import date as datetime_date
    product = check_str_element(obj, 'product', '产品')
    assert product in PRODUCT_NAME_RANGE, str(obj)
    date = obj.get('date')
    assert isinstance(date, datetime_date), str(obj)
    check_str_element(obj, 'institution', '机构')
    currency = check_str_element(obj, 'currency', '账户结算币种')
    obj['currency'] = CURRENCY_RANGE_MAP[currency]


def check_security_info(secu_obj: dict):
    account_type = check_str_element(secu_obj, 'account_type', '账户类型')
    security_code = check_str_element(secu_obj, 'security_code', '证券代码')
    if '普通账户' in account_type or '两融账户' in account_type:  # @waves
        if '.' not in security_code:
            if len(security_code) == 6:
                if security_code[0] in ('6', '5', '7'):
                    secu_obj['security_code'] = '.'.join([security_code, 'SH'])
                elif security_code[0] in ('0', '3',):
                    secu_obj['security_code'] = '.'.join([security_code, 'SZ'])
                elif security_code[:3] in ('110', '113', '132'):
                    secu_obj['security_code'] = '.'.join([security_code, 'SH'])
                elif security_code[:3] in ('128', 'jm3389',):
                    secu_obj['security_code'] = '.'.join([security_code, 'SZ'])
                elif security_code[:5] in ('20400',):
                    secu_obj['security_code'] = '.'.join([security_code, 'SH'])
                elif security_code in ('127045', '127047'):
                    secu_obj['security_code'] = '.'.join([security_code, 'SZ'])
                elif security_code[0] == 'P':
                    secu_obj['security_code'] = '.'.join([security_code, 'SZ'])
                elif security_code == '889688' or security_code == '871245':
                    secu_obj['security_code'] = '.'.join(['871245', 'SZ'])
                elif security_code == '889086' or security_code == '831689':
                    secu_obj['security_code'] = '.'.join(['831689', 'NQ'])
                elif security_code == '889699' or security_code == '832419':
                    secu_obj['security_code'] = '.'.join(['832419', 'BJ'])
                elif security_code == '889007' or security_code == '873169':
                    secu_obj['security_code'] = '.'.join(['873169', 'BJ'])
                elif security_code == '889666' or security_code == '833580':
                    secu_obj['security_code'] = '.'.join(['833580', 'BJ'])
                elif security_code == '889000' or security_code == '871970':
                    secu_obj['security_code'] = '.'.join(['871970', 'BJ'])
                elif security_code == '889886' or security_code == '833533':
                    secu_obj['security_code'] = '.'.join(['833533', 'BJ'])
                elif security_code == '889899' or security_code == '831167':
                    secu_obj['security_code'] = '.'.join(['831167', 'BJ'])
                elif security_code == '889866' or security_code == '838171':
                    secu_obj['security_code'] = '.'.join(['838171', 'BJ'])
                elif security_code == '873223' or security_code == '889223':
                    secu_obj['security_code'] = '.'.join(['873223', 'BJ'])
                elif security_code == '870299' or security_code == '889668':
                    secu_obj['security_code'] = '.'.join(['870299', 'BJ'])
                elif security_code == '889968' or security_code == '832491':
                    secu_obj['security_code'] = '.'.join(['832491', 'BJ'])
                elif security_code == '889369' or security_code == '430564':
                    secu_obj['security_code'] = '.'.join(['430564', 'BJ'])
                elif security_code == '889278' or security_code == '831278':
                    secu_obj['security_code'] = '.'.join(['831278', 'BJ'])
                elif security_code == '889669' or security_code == '833943':
                    secu_obj['security_code'] = '.'.join(['833943', 'BJ'])  # 优机股份
                elif security_code == '889131' or security_code == '838670':
                    secu_obj['security_code'] = '.'.join(['838670', 'BJ'])  # 恒进感应
                elif security_code == '837821' or security_code == '889821':
                    secu_obj['security_code'] = '.'.join(['837821', 'BJ'])  #  则成电子
                else:
                    raise NotImplementedError(secu_obj)
            elif len(security_code) == 5:
                if security_code[0] in ('0',):
                    secu_obj['security_code'] = '.'.join([security_code[1:], 'HK'])
                else:
                    raise NotImplementedError(secu_obj)
            elif len(security_code) == 0 or len(security_code) == 1:
                secu_obj['security_code'] = ''
            elif len(re.sub(r'\W', '', security_code)) == 0:
                secu_obj['security_code'] = ''
            elif secu_obj['security_code'] == re.sub('-', '', str(secu_obj['date'])):
                # res = secu_obj['security_code'] == secu_obj['date']
                # print(type(str(secu_obj['date'])))
                # str_date = str(secu_obj['date'])
                # print(str_date)
                # res_r = re.sub('-','',str(secu_obj['date']))
                secu_obj['security_code'] = ''
            else:
                raise NotImplementedError(secu_obj)
    elif account_type == '中信港股':
        assert '.' in security_code, secu_obj
        assert security_code.endswith('HK'), secu_obj
    elif account_type == '中信美股':
        assert '.' in security_code, secu_obj
        if security_code.endswith('.OQ'):
            secu_obj['security_code'] = security_code.replace('.OQ', '.O')
        elif security_code.endswith('.N'):
            pass
        else:
            raise NotImplementedError(secu_obj)
    elif '期货' in account_type:
        assert '.' not in security_code, secu_obj
        if security_code.upper()[:2] in ('IH', 'IF', 'IC'):
            secu_obj['security_code'] = '.'.join([security_code, 'CFE'])
        else:
            raise NotImplementedError(secu_obj)
    elif '期权' in account_type:
        if '.' not in security_code:
            assert security_code.startswith('100'), secu_obj
            secu_obj['security_code'] = '.'.join([security_code, 'SH'])
        else:
            raise NotImplementedError(secu_obj)
    else:
        raise NotImplementedError(secu_obj)
    if len(re.sub(r'\W', '', security_code)) == 0:
        pass
    else:
        try:
            check_str_element(secu_obj, 'security_name', '证券名称').strip()
        except AssertionError:
            pass
    # if '普通账户' in account_type or account_type in ('中信美股', '中信港股', ):
    #
    # elif '两融账户' in account_type:
    #     pass
    # elif
    # else:
    #     raise NotImplementedError(secu_obj)


def check_trade_info(trade_obj: dict):
    trade_class = check_str_element(trade_obj, 'trade_class', '交易类别')
    if '费' in trade_class \
            or trade_class in NORMAL_BLANK_SECURITY_TRADE_CLASS_ALLOWANCE:
        trade_price, trade_volume = 0.0, 0.0
    else:
        trade_price = check_float_element(trade_obj, 'trade_price', '交易价格')
        trade_volume = check_float_element(trade_obj, 'trade_volume', '交易数量')
    try:
        trade_amount = check_float_element(trade_obj, 'trade_amount', '交易额')
    except AssertionError:
        trade_amount = trade_price * trade_volume
        trade_obj['trade_amount'] = trade_amount
    check_float_element(trade_obj, 'cash_move', '资金变动数量')
    if trade_class in ('ETF现金替代退款', '股息入账'):
        return True
    assert check_multiply_match(abs(trade_price), abs(trade_volume), abs(trade_amount)), str(trade_obj)


def clear_str_content(str_for_read: str):
    return str_for_read.replace('五 粮 液', '五粮液').replace('港股通组合费收取', '、  、  港股通组合费收取')


def derive_product_name(product_expression):
    product = None
    if '静康' in product_expression:
        raise NotImplementedError(product_expression)
    if '创新' in product_expression:
        for tag in PRODUCT_NAME_RANGE:
            if tag in product_expression and '创新' in tag:
                product = tag
                break
            else:
                continue
    else:
        for tag in PRODUCT_NAME_RANGE:
            if tag in product_expression:
                assert '创新' not in tag
                product = tag
                break
            else:
                continue
    assert product is not None, '无法获取产品名称 {}'.format(product_expression)
    assert product in PRODUCT_NAME_RANGE, '未知产品名称 {}'.format(product_expression)
    return product


# ================================ [NORMAL] ================================ #
def confirm_normal_account(acc_obj: dict):
    """检查普通账户的账户信息是否合法"""
    check_basic_info(acc_obj)
    if acc_obj['product'] == '专享16号':
        print("tyx")
    cash_amount = check_float_element(acc_obj, 'cash_amount', '现金')
    capital_sum = check_float_element(acc_obj, 'capital_sum', '资产总额')
    market_sum = check_float_element(acc_obj, 'market_sum', '市值总额')
    check_float_element(acc_obj, 'cash_available', '可用资金', blank_skip=True)

    assert check_addition_match(cash_amount, market_sum, capital_sum), '{} {}'.format(
        capital_sum - market_sum - cash_amount, acc_obj
    )


def confirm_normal_position(pos_obj: dict):
    check_basic_info(pos_obj)
    check_security_info(pos_obj)
    check_float_element(pos_obj, 'hold_volume', '持仓数量')
    check_float_element(pos_obj, 'market_value', '市值')
    check_float_element(pos_obj, 'total_cost', '', blank_skip=True)
    check_float_element(pos_obj, 'close_price', '', blank_skip=True)
    check_float_element(pos_obj, 'weight_average_cost', '', blank_skip=True)
    offset = check_str_element(pos_obj, 'offset', '多空方向')
    assert offset in (OFFSET_OPEN, OFFSET_CLOSE), str(pos_obj)


def confirm_normal_flow(flow_obj: dict):
    check_basic_info(flow_obj)
    check_trade_info(flow_obj)
    trade_class = str_check(flow_obj['trade_class'])
    if trade_class in NORMAL_BLANK_SECURITY_TRADE_CLASS_ALLOWANCE \
            or '组合费' in trade_class:
        pass
    elif trade_class in MARGIN_BLANK_SECURITY_TRADE_CLASS_ALLOWANCE:
        pass
    else:
        check_security_info(flow_obj)


def confirm_normal_flow_list(flow_list: list):
    for obj in flow_list:
        confirm_normal_flow(obj)


def match_normal_pos_acc(pos_list: list, acc_obj: dict):
    confirm_normal_account(acc_obj)
    market_value = 0.0
    flag = True
    for pos in pos_list:
        flag = False
        assert isinstance(pos, dict), str(pos)
        confirm_normal_position(pos)
        assert check_str_element(acc_obj, 'product') == check_str_element(pos, 'product'), '{}\n{}'.format(acc_obj, pos)
        assert date_check(acc_obj['date']) == date_check(pos['date']), '{}\n{}'.format(acc_obj, pos)
        assert str_check(acc_obj['institution']) == str_check(pos['institution']), '{}\n{}'.format(acc_obj, pos)
        market_value += pos['market_value']
    if flag:
        market_value = acc_obj['market_sum']
    if acc_obj['account_type'] == '华创普通账户':
        acc_obj['market_sum'] = market_value
    if acc_obj['institution'] == '兴业' and acc_obj['product'] == '专享17号':
        acc_obj['market_sum'] = market_value
    if acc_obj['institution'] == '国君' and acc_obj['product'] == '稳健1号':
        acc_obj['market_sum'] = market_value
    if acc_obj['institution'] == '长江' and acc_obj['product'] == '久铭300指数':
        acc_obj['market_sum'] = market_value
    if acc_obj['institution'] == '安信':
        acc_obj['market_sum'] = market_value
    assert not is_different_float(
        market_value, float_check(acc_obj['market_sum']), gap=1
    ), '{} : added {} ~ readed {}\n{}\n{}'.format(
        market_value - acc_obj['market_sum'],
        market_value, acc_obj['market_sum'],
        acc_obj, '\n'.join([str(var) for var in pos_list]))


# ================================ [MARGIN] ================================ #
def confirm_margin_account(acc_obj: dict):
    confirm_normal_account(acc_obj)
    check_float_element(acc_obj, 'net_asset', '净资产', blank_skip=True)
    total_liability = check_float_element(acc_obj, 'total_liability', '融资负债')
    liability_principal = check_float_element(acc_obj, 'liability_principal', '融资本金')
    liability_amount_interest = check_float_element(acc_obj, 'liability_amount_interest', '融资应付利息')
    liability_amount_fee = check_float_element(acc_obj, 'liability_amount_fee', '融资费用')
    liability_amount_for_pay = check_float_element(acc_obj, 'liability_amount_for_pay', '待扣除资金')
    # assert check_addition_match(
    #     liability_amount_fee + liability_amount_interest + liability_amount_for_pay,
    #     liability_principal, total_liability
    # ), '两融负债检查失败 \n{}'.format(acc_obj)


def confirm_margin_flow_list(flow_list: list):
    for obj in flow_list:
        confirm_normal_flow(obj)


def confirm_margin_liability(lia_obj: dict):
    check_basic_info(lia_obj)
    check_str_element(lia_obj, 'security_code', '证券代码')
    # check_security_info(lia_obj)
    check_str_element(lia_obj, 'contract_date', '合约日期')
    check_str_element(lia_obj, 'contract_type', '合约类型')
    check_float_element(lia_obj, 'contract_volume', '合约数量')
    check_float_element(lia_obj, 'contract_amount', '合约金额')
    check_float_element(lia_obj, 'interest_payable', '应付利息')
    check_float_element(lia_obj, 'fee_payable', '应付费用')
    check_str_element(lia_obj, 'payback_date', '截止日')


def match_margin_pos_acc(pos_list: list, acc_obj: dict):
    confirm_margin_account(acc_obj)
    market_value = 0.0
    for pos in pos_list:
        assert isinstance(pos, dict), str(pos)
        confirm_normal_position(pos)
        assert check_str_element(acc_obj, 'product') == check_str_element(pos, 'product'), '{}\n{}'.format(acc_obj, pos)
        assert date_check(acc_obj['date']) == date_check(pos['date']), '{}\n{}'.format(acc_obj, pos)
        assert str_check(acc_obj['institution']) == str_check(pos['institution']), '{}\n{}'.format(acc_obj, pos)
        market_value += float_check(pos['market_value'])
    assert not is_different_float(
        market_value, float_check(acc_obj['market_sum']), gap=1
    ), '{} : {} ~ {}\n{}\n{}'.format(
        market_value - acc_obj['market_sum'],
        market_value, acc_obj['market_sum'],
        acc_obj, '\n'.join([str(var) for var in pos_list]))


def match_margin_liability_acc(liability_list: list, acc_obj: dict):
    confirm_margin_account(acc_obj)
    liability_amount, liability_volume = 0.0, 0.0
    for lia in liability_list:
        assert isinstance(lia, dict), str(lia)
        confirm_margin_liability(lia)
        assert check_str_element(acc_obj, 'product') == check_str_element(lia, 'product'), '{}\n{}'.format(acc_obj, lia)
        assert date_check(acc_obj['date']) == date_check(lia['date']), '{}\n{}'.format(acc_obj, lia)
        assert str_check(acc_obj['institution']) == str_check(lia['institution']), '{}\n{}'.format(acc_obj, lia)
        liability_amount += float_check(lia['contract_amount'])
    # assert not is_different_float(
    #     liability_amount, float_check(acc_obj['liability_principal'])
    # ), '{}\n{}'.format(acc_obj, liability_list)


# ================================ [FUTURE] ================================ #
def confirm_future_account(acc_obj: dict):
    check_basic_info(acc_obj)
    cash_amount = check_float_element(acc_obj, 'cash_amount', '可用资金')
    capital_sum = check_float_element(acc_obj, 'capital_sum', '期末结存')
    market_sum = check_float_element(acc_obj, 'market_sum', '保证金占用')

    assert check_addition_match(cash_amount, market_sum, capital_sum), str(acc_obj)

    last_capital_sum = check_float_element(acc_obj, 'last_capital_sum', '前日结存')
    market_pl = check_float_element(acc_obj, 'market_pl', '盯市盈亏')
    realized_pl = check_float_element(acc_obj, 'realized_pl', '平仓盈亏')
    trade_fee = check_float_element(acc_obj, 'trade_fee', '手续费')
    out_in_cash = check_float_element(acc_obj, 'out_in_cash', '出入金')
    if acc_obj['product'] == '稳健22号' and acc_obj['institution'] == '银河期货':
        pass
    else:
        if acc_obj['product'] == '创新稳健5号' and acc_obj['institution'] == '银河期货':
            pass
        elif acc_obj['product'] == '久铭1号' and acc_obj['institution'] == '建信期货':
            pass
        else:
            assert check_addition_match(
                last_capital_sum, market_pl + realized_pl + out_in_cash - trade_fee, capital_sum,
            ), acc_obj


def confirm_future_position(pos_obj: dict):
    check_basic_info(pos_obj)
    check_security_info(pos_obj)
    check_float_element(pos_obj, 'long_position', '买持')
    check_float_element(pos_obj, 'short_position', '卖持')
    check_float_element(pos_obj, 'buy_average_cost', '买均价')
    check_float_element(pos_obj, 'sell_average_cost', '卖均价')
    check_float_element(pos_obj, 'prev_settlement', '昨结算')
    check_float_element(pos_obj, 'settlement_price', '结算价')
    check_float_element(pos_obj, 'market_pl', '盯市盈亏')
    check_str_element(pos_obj, 'investment_tag', '投保')
    check_float_element(pos_obj, 'margin', '保证金占用')
    pos_obj['long_mkv'], pos_obj['short_mkv'] = 0, 0
    # check_float_element(pos_obj, 'long_mkv', '多头期权市值')
    # check_float_element(pos_obj, 'short_mkv', '空头期权市值')
    check_str_element(pos_obj, 'currency', '币种')


def confirm_future_flow_list(flow_list: list):
    for d_obj in flow_list:
        check_basic_info(d_obj)
        check_security_info(d_obj)
        check_str_element(d_obj, 'offset', '开平'), str(d_obj)
        check_str_element(d_obj, 'investment_tag', '投保'), str(d_obj)
        check_float_element(d_obj, 'trade_price', '价格'), str(d_obj)
        check_float_element(d_obj, 'trade_volume', '数量'), str(d_obj)
        check_float_element(d_obj, 'trade_amount', '成交量'), str(d_obj)
        check_float_element(d_obj, 'trade_fee', '手续费'), str(d_obj)
        d_obj['trade_class'] = check_str_element(d_obj, 'trade_class', '业务标志').strip()


def match_future_pos_acc(pos_list: list, acc_obj: dict):
    confirm_future_account(acc_obj)

    market_value = 0.0
    for pos in pos_list:
        assert isinstance(pos, dict), str(pos)
        confirm_future_position(pos)
        assert check_str_element(acc_obj, 'product') == check_str_element(pos, 'product'), '{}\n{}'.format(acc_obj, pos)
        assert date_check(acc_obj['date']) == date_check(pos['date']), '{}\n{}'.format(acc_obj, pos)
        assert str_check(acc_obj['institution']) == str_check(pos['institution']), '{}\n{}'.format(acc_obj, pos)
        market_value += float_check(pos['margin'])
    assert not is_different_float(
        market_value, float_check(acc_obj['market_sum']), gap=1
    ), '{}\n{}'.format(acc_obj, pos_list)


# ================================ [OPTION] ================================ #
def confirm_option_account(acc_obj: dict):
    check_basic_info(acc_obj)
    check_float_element(acc_obj, 'cash_available', '可用资金', blank_skip=True)
    cash_amount = check_float_element(acc_obj, 'cash_amount', '现金资产')
    capital_sum = check_float_element(acc_obj, 'capital_sum', '总权益')
    market_sum = check_float_element(acc_obj, 'market_sum', '期权市值')
    assert check_addition_match(cash_amount, market_sum, capital_sum), str(acc_obj)


def confirm_option_position(pos_obj: dict):
    check_basic_info(pos_obj)
    check_security_info(pos_obj)
    warehouse_class = check_str_element(pos_obj, 'warehouse_class', '持仓类别')
    assert warehouse_class in ('权利方', '义务方'), pos_obj
    check_float_element(pos_obj, 'hold_volume', '持仓数量')
    check_float_element(pos_obj, 'average_cost', '均价', blank_skip=True)
    check_float_element(pos_obj, 'settlement_price', '结算价')
    check_float_element(pos_obj, 'market_value', '期权市值')
    check_str_element(pos_obj, 'currency', '币种')


def confirm_option_flow_list(flow_list: list):
    for d_obj in flow_list:
        check_basic_info(d_obj)
        check_security_info(d_obj)
        check_str_element(d_obj, 'warehouse_class', '持仓类别')
        check_str_element(d_obj, 'offset', '开平')
        check_str_element(d_obj, 'trade_class', '买卖方向')
        check_float_element(d_obj, 'trade_price', '价格')
        check_float_element(d_obj, 'trade_volume', '数量')
        check_float_element(d_obj, 'trade_amount', '成交金额')
        check_float_element(d_obj, 'cash_move', '资金发生数')
        check_float_element(d_obj, 'trade_fee', '手续费'), str(d_obj)
        check_str_element(d_obj, 'reserve_tag', '备兑标志')
        check_str_element(d_obj, 'customer_id', 'customer_id', blank_skip=True)
        check_str_element(d_obj, 'capital_account', 'capital_account', blank_skip=True)
        d_obj['trade_class'] = check_str_element(d_obj, 'trade_class', '业务标志').strip()


def match_option_pos_acc(pos_list: list, acc_obj: dict):
    confirm_option_account(acc_obj)
    market_value = 0.0
    for pos in pos_list:
        assert isinstance(pos, dict), str(pos)
        confirm_option_position(pos)
        assert check_str_element(acc_obj, 'product') == check_str_element(pos, 'product'), '{}\n{}'.format(acc_obj, pos)
        assert date_check(acc_obj['date']) == date_check(pos['date']), '{}\n{}'.format(acc_obj, pos)
        assert str_check(acc_obj['institution']) == str_check(pos['institution']), '{}\n{}'.format(acc_obj, pos)
        market_value += float_check(pos['market_value'])
    assert not is_different_float(
        market_value, float_check(acc_obj['market_sum']), gap=1
    ), '{} - {}\n{}\n{}'.format(market_value, float_check(acc_obj['market_sum']), acc_obj, pos_list)


# ================================ [SWAP] ================================ #
def confirm_swap_citic_calculation(calculation: dict):
    check_str_element(calculation, 'trade_currency', '交易货币')
    settle_currency = check_str_element(calculation, 'settle_currency', '结算货币')
    assert settle_currency.upper() == 'CNY', str(calculation)
    check_float_element(calculation, 'exchange_rate', '汇率')
    check_float_element(calculation, 'notional_principle_origin', '组合名义本金额加总的近似值交易货币')
    check_float_element(calculation, 'prepaid_balance_origin', '预付金余额加总近似值交易货币')
    check_float_element(calculation, 'capital_sum_origin', '盯市金额加总的近似值交易货币')
    check_float_element(calculation, 'capital_sum', '盯市金额加总的近似值结算货币')
    check_float_element(calculation, 'initial_margin_origin', '初始保障金额加总的近似值交易货币')
    check_float_element(calculation, 'maintenance_margin_origin', '维持保障金额加总的近似值交易货币')
    check_float_element(calculation, 'accumulated_interest_accrued', '累计利率收益金额和预付金返息金额的加总近似值交易货币')
    check_float_element(calculation, 'accumulated_interest_payed', '应付已付利率收益金额和预付金返息金额加总的近似值交易货币')


def confirm_swap_citic_balance(balance: dict):
    check_str_element(balance, 'trade_currency', '交易货币')
    settle_currency = check_str_element(balance, 'settle_currency', '结算货币')
    assert settle_currency.upper() == 'CNY', str(balance)
    check_float_element(balance, 'accumulated_withdrawal', '累计支取预付金净额结算货币')
    check_float_element(balance, 'carryover_balance_origin', '结转预付金余额交易货币')
    check_float_element(balance, 'exchange_rate', '汇率')
    check_float_element(balance, 'total_balance', '预付金余额加总近似值交易货币')
    check_float_element(balance, 'available_balance', '可用保障金额加总近似值交易货币')


def confirm_swap_citic_underlying(underlying_obj: dict):
    check_str_element(underlying_obj, 'trade_currency', '交易货币')
    check_security_info(underlying_obj)
    check_str_element(underlying_obj, 'offset', '标的方向多空')
    hold_volume = check_float_element(underlying_obj, 'hold_volume', '标的数量')
    check_float_element(underlying_obj, 'contract_multiplier', '标的乘数')
    # check_str_element(underlying_obj, 'average_cost_origin', '平均单位持仓成本交易货币')
    check_float_element(underlying_obj, 'total_cost_origin', '该标的持仓成本加总的近似值交易货币')
    check_float_element(underlying_obj, 'accumulated_realized_profit', '组合累计实现收益加总近似值交易货币')
    check_float_element(underlying_obj, 'accumulated_unrealized_profit', '组合待实现收益加总近似值交易货币')
    try:
        check_float_element(underlying_obj, 'market_value_origin', '标的市值交易货币')
    except AssertionError as a_e:
        if abs(hold_volume) < 0.01:
            underlying_obj['market_value_origin'] = 0.0
        else:
            raise a_e


def match_swap_citic(balance: dict, calculation: dict, underlying_list: list):
    confirm_swap_citic_balance(balance)
    confirm_swap_citic_calculation(calculation)
    market_value = 0.0
    for pos in underlying_list:
        confirm_swap_citic_underlying(pos)
        market_value += pos['market_value_origin']
    assert balance['trade_currency'] == calculation['trade_currency'], '{}\n{}'.format(balance, calculation)
    assert balance['settle_currency'] == calculation['settle_currency'], '{}\n{}'.format(balance, calculation)
    # 累计支取预付金净额CNY/汇率 - 已付利息USD + 市值总额USD = 预付金余额USD
    # 市值USD + 预付金可用余额USD（存出保证金） - 应付利息 = 町市金额USD
    # 预付金可用余额USD = 累计支取预付金净额CNY/汇率 + 结转预付金余额USD - 初始保障金额USD
    calculated_cash = balance['accumulated_withdrawal'] / balance['exchange_rate'] \
                      + balance['carryover_balance_origin'] - calculation['initial_margin_origin']
    calculated_interest_payable = abs(calculation['accumulated_interest_accrued']) \
                                  - abs(calculation['accumulated_interest_payed'])

    assert check_addition_match(
        calculated_cash - calculated_interest_payable, market_value, calculation['capital_sum_origin'],
        error_percent=0.05,
    ), '{}\n{}\n{}'.format(balance, calculation, underlying_list)
    assert check_multiply_match(
        calculation['capital_sum_origin'], calculation['exchange_rate'], calculation['capital_sum'],
        error_abs=1,
    ), '{}'.format(calculation)
