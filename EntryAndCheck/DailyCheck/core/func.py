# -*- encoding: UTF-8 -*-
# ---------------------------------import------------------------------------
import datetime

from modules.AccountPosition import AccountPosition

from jetend.modules.jmInfoBoard import jmInfoBoard
from jetend.structures import List
from jetend.DataCheck import *
from extended.Logger import LogWrapper


def handle_account_payable_receivable_by_ta_flow(acc_pos: List, ta_flow: List, date: datetime.date, ):
    from modules.Information import TaFlow
    acc_list = List()

    for flow in ta_flow:
        assert isinstance(flow, TaFlow)

        if flow.date != date:
            continue

        # 作为被申赎方
        if flow.trade_class in ('赎回', '赎回业绩报酬', '计提业绩报酬', '业绩报酬计提',):  # 客户发起赎回，确认前无操作
            pass

        elif flow.trade_class in ('申购', '认购'):  # 客户发起申购，确认前需要增加应付申购款并检查资金是否到账
            acc_list.append(AccountPosition(
                product=flow.security_name, date=date, account_name='应付申购款', institution=flow.investor,
                security_code='-', currency_origin='RMB', currency='RMB',
                volume=abs(flow.trade_amount),
            ))
            if flow.id_number is None:
                pass
            elif len(flow.id_number) == 6:
                try:
                    acc_obj = acc_pos.find_value(
                        product=flow.investor, account_name='待确认申购款', security_name=flow.security_name,
                    )
                    acc_obj.volume = acc_obj.volume + abs(flow.trade_amount)
                except ValueError:
                    acc_list.append(AccountPosition(
                        product=flow.investor, date=date, account_name='待确认申购款', institution='久铭',
                        security_code='-', security_name=flow.security_name, volume=abs(flow.trade_amount),
                        currency_origin='RMB', currency='RMB',
                    ))
                except TypeError as type_error:
                    continue
                    print(flow.__dict__)
                    raise type_error
            else:
                pass
        elif flow.trade_class == '基金转入':
            if '创新' in flow.security_name:
                pass
            else:
                acc_list.append(AccountPosition(
                    product=flow.security_name, date=date, account_name='应付申购款', institution=flow.investor,
                    security_code='-', currency_origin='RMB', currency='RMB',
                    volume=abs(flow.trade_amount),
                ))
            if len(flow.id_number) == 6:
                try:
                    acc_obj = acc_pos.find_value(
                        product=flow.investor, account_name='待确认申购款', security_name=flow.security_name,
                    )
                    acc_obj.volume = acc_obj.volume + abs(flow.trade_amount)
                except ValueError:
                    acc_list.append(AccountPosition(
                        product=flow.investor, date=date, account_name='待确认申购款', institution='久铭',
                        security_code='-', security_name=flow.security_name, volume=abs(flow.trade_amount),
                        currency_origin='RMB', currency='RMB',
                    ))
        elif flow.trade_class == '基金转出':
            if '创新' in flow.security_name:  # 暂时不处理创新系列产品
                pass
            else:  # 相当与赎回
                pass
                # raise NotImplementedError(flow)
            if '久铭' in flow.investor:
                raise NotImplementedError(flow)
        else:
            raise NotImplementedError(flow)

    return acc_list


def handle_fund_share_by_ta_confirm_flow(
        last_acc_pos: List, acc_pos: List, ta_confirm_flow: List, date: datetime.date,
):
    """
    处理申赎确认流水得到实收基金
        * 更新银行存款
        * 更新实收基金
    :return: List - 实收基金、银行存款
    """
    from modules.Information import TaFlow
    acc_list = List()

    for last_share_acc in last_acc_pos.find_value_where(account_name='实收基金'):
        assert isinstance(last_share_acc, AccountPosition)

        share_acc = AccountPosition().update(last_share_acc)
        assert share_acc.account_name == '实收基金', '运行日实收基金对象出错 {}'.format(last_share_acc)
        share_acc.date = date

        for flow in ta_confirm_flow.find_value_where(security_name=last_share_acc.product):  # 考虑该产品作为被赎回方
            assert isinstance(flow, TaFlow)
            if flow.trade_class == '赎回':  # 投资者赎回当前产品，应付赎回款增加，实收基金减少
                share_acc.volume = share_acc.volume - abs(flow.trade_volume)
                assert share_acc.currency == 'RMB', '{}'.format(share_acc)
                if flow.sales_agency == '直销':
                    money_belonging = flow.investor
                else:
                    money_belonging = flow.sales_agency
                try:
                    tar_obj = acc_pos.find_value(
                        product=share_acc.product, account_name='应付赎回款', institution=money_belonging, )
                    tar_obj.volume = tar_obj.volume + abs(flow.trade_amount)
                except ValueError:
                    try:
                        tar_obj = acc_list.find_value(
                            product=share_acc.product, account_name='应付赎回款', institution=money_belonging, )
                        tar_obj.volume = tar_obj.volume + abs(flow.trade_amount)
                    except ValueError:
                        acc_list.append(AccountPosition(
                            product=share_acc.product, date=date, account_name='应付赎回款', institution=money_belonging,
                            security_code='-', volume=abs(flow.trade_amount),
                            currency_origin=share_acc.currency, currency=share_acc.currency,
                        ))
            elif flow.trade_class == '申购':  # 投资者申购当前产品，实收基金增加，应付申购款消除
                share_acc.volume = share_acc.volume + abs(flow.trade_volume)

                try:
                    tar_obj = acc_pos.find_value(
                        product=share_acc.product, account_name='应付申购款',
                        institution=flow.investor,
                    )
                except ValueError:
                    raise RuntimeError('确认未知应付申购款 {}'.format(flow))
                if not is_different_float(tar_obj.volume, flow.trade_amount, gap=10):
                    tar_obj.volume = 0.0
                else:
                    tar_obj.volume = tar_obj.volume - abs(flow.trade_amount)
            elif flow.trade_class == '赎回业绩报酬':
                share_acc.volume = share_acc.volume - abs(flow.trade_volume)
                assert share_acc.currency == 'RMB', '{}'.format(share_acc)
                try:
                    tar_obj = acc_pos.find_value(product=share_acc.product, account_name='累计应付业绩报酬', )
                    tar_obj.volume = tar_obj.volume + abs(flow.trade_amount)
                except ValueError:
                    try:
                        tar_obj = acc_list.find_value(product=share_acc.product, account_name='累计应付业绩报酬', )
                        tar_obj.volume = tar_obj.volume + abs(flow.trade_amount)
                    except ValueError:
                        tar_obj = AccountPosition(
                            product=share_acc.product, date=date, account_name='累计应付业绩报酬', institution='久铭',
                            security_code='-', volume=abs(flow.trade_amount),
                            currency_origin=share_acc.currency, currency=share_acc.currency,
                        )
                        acc_list.append(tar_obj)
            elif flow.trade_class.strip() in ('计提业绩报酬',):
                if flow.trade_volume < 0:
                    share_acc.volume = share_acc.volume - abs(flow.trade_volume)
                    assert share_acc.currency == 'RMB', '{}'.format(share_acc)
                    try:
                        tar_obj = acc_pos.find_value(product=share_acc.product, account_name='累计应付业绩报酬', )
                        tar_obj.volume = tar_obj.volume + abs(flow.trade_amount)
                    except ValueError:
                        try:
                            tar_obj = acc_list.find_value(product=share_acc.product, account_name='累计应付业绩报酬', )
                            tar_obj.volume = tar_obj.volume + abs(flow.trade_amount)
                        except ValueError:
                            tar_obj = AccountPosition(
                                product=share_acc.product, date=date, account_name='累计应付业绩报酬', institution='久铭',
                                security_code='-', volume=abs(flow.trade_amount),
                                currency_origin=share_acc.currency, currency=share_acc.currency,
                            )
                            acc_list.append(tar_obj)
                elif flow.trade_volume > 0:
                    share_acc.volume = share_acc.volume + abs(flow.trade_volume)
                    assert share_acc.currency == 'RMB', '{}'.format(share_acc)
                    try:
                        tar_obj = acc_pos.find_value(product=share_acc.product, account_name='累计应付业绩报酬', )
                        tar_obj.volume = tar_obj.volume - abs(flow.trade_amount)
                    except ValueError:
                        try:
                            tar_obj = acc_list.find_value(product=share_acc.product, account_name='累计应付业绩报酬', )
                            tar_obj.volume = tar_obj.volume - abs(flow.trade_amount)
                        except ValueError:
                            raise RuntimeError('转出未知份额 {}'.format(flow))
                            # tar_obj = AccountPosition(
                            #     product=share_acc.product, date=date, account_name='累计应付业绩报酬', institution='久铭',
                            #     security_code='-', volume=abs(flow.trade_amount),
                            #     currency_origin=share_acc.currency, currency=share_acc.currency,
                            # )
                            # acc_list.append(tar_obj)
                else:
                    raise NotImplementedError(flow)
            elif flow.trade_class == '基金转出':
                share_acc.volume = share_acc.volume - abs(flow.trade_volume)
                try:
                    tar_obj = acc_pos.find_value(account_name='应付赎回款', institution='待转换', )
                    tar_obj.volume = tar_obj.volume + abs(flow.trade_amount)
                except ValueError:
                    try:
                        tar_obj = acc_list.find_value(account_name='应付赎回款', institution='待转换', )
                        tar_obj.volume = tar_obj.volume + abs(flow.trade_amount)
                    except ValueError:
                        acc_list.append(AccountPosition(
                            product=share_acc.product, date=date, account_name='应付赎回款', institution='待转换',
                            security_code='-', volume=abs(flow.trade_amount),
                            currency_origin=share_acc.currency, currency=share_acc.currency,
                        ))
            elif flow.trade_class == '基金转入':  # 投资者申购当前产品，实收基金增加，应付申购款消除
                share_acc.volume = share_acc.volume + abs(flow.trade_volume)
                try:
                    tar_obj = acc_pos.find_value(
                        product=share_acc.product, account_name='应付申购款', institution=flow.investor,
                    )
                except ValueError:
                    raise RuntimeError('确认未知应付申购款 {}'.format(flow))
                if not is_different_float(tar_obj.volume, flow.trade_amount, gap=10):
                    tar_obj.volume = 0.0
                else:
                    tar_obj.volume = tar_obj.volume - abs(flow.trade_amount)
            else:
                raise NotImplementedError(flow)

        for flow in ta_confirm_flow.find_value_where(investor=last_share_acc.product):  # 考虑产品作为申赎自有产品方
            assert isinstance(flow, TaFlow)

            if flow.trade_class == '赎回':
                pos = acc_pos.find_value(
                    product=share_acc.product, account_name='自有产品', security_name=flow.security_name)
                pos.volume = pos.volume - abs(flow.trade_volume)
                try:
                    obj = acc_pos.find_value(
                        product=share_acc.product, account_name='其他应收款', institution='基金投资',
                        security_code=pos.security_code,
                    )
                    obj.volume = obj.volume + abs(flow.trade_amount)
                except ValueError:
                    try:
                        obj = acc_list.find_value(
                            product=share_acc.product, account_name='其他应收款', institution='基金投资',
                            security_code=pos.security_code,
                        )
                        obj.volume = obj.volume + abs(flow.trade_amount)
                    except ValueError:
                        acc_list.append(AccountPosition(
                            product=share_acc.product, date=date, account_name='其他应收款', institution='基金投资',
                            security_code=pos.security_code, security_name=pos.security_name,
                            volume=abs(flow.trade_amount),
                            currency_origin=share_acc.currency, currency=share_acc.currency,
                        ))
            elif flow.trade_class == '申购':  # 申购其他产品被确认，待确认申购款转持仓
                try:
                    for_confirm_obj = acc_pos.find_value(
                        product=share_acc.product, account_name='待确认申购款', security_name=flow.security_name
                    )
                except ValueError:
                    raise RuntimeError('无待确认申购款 {}\n{}\n{}'.format(share_acc.product, flow, acc_pos))
                if abs(abs(for_confirm_obj.volume) - abs(flow.trade_amount)) < 1:
                    for_confirm_obj.volume = 0.0
                else:
                    for_confirm_obj.volume = for_confirm_obj.volume - abs(flow.trade_amount)
                    assert for_confirm_obj.volume >= 0, str(for_confirm_obj)
                try:
                    confirmed_position = acc_pos.find_value(
                        product=share_acc.product, account_name='自有产品', security_name=flow.security_name,
                    )
                    confirmed_position.volume = confirmed_position.volume + abs(flow.trade_volume)
                except ValueError:
                    acc_list.append(AccountPosition(
                        product=share_acc.product, date=date, account_name='自有产品', institution='久铭',
                        security_code='-', security_name=flow.security_name, volume=abs(flow.trade_volume),
                        currency_origin=share_acc.currency, currency=share_acc.currency,
                    ))
            elif flow.trade_class.strip() in ('计提业绩报酬',):
                pos = acc_pos.find_value(
                    product=share_acc.product, account_name='自有产品', security_name=flow.security_name)
                pos.volume = pos.volume - abs(flow.trade_volume)
                try:
                    obj = acc_pos.find_value(
                        product=share_acc.product, account_name='其他应收款', institution='业绩报酬',
                        security_code=pos.security_code,
                    )
                    obj.volume = obj.volume + abs(flow.trade_amount)
                except ValueError:
                    try:
                        obj = acc_list.find_value(
                            product=share_acc.product, account_name='其他应收款', institution='业绩报酬',
                            security_code=pos.security_code,
                        )
                        obj.volume = obj.volume + abs(flow.trade_amount)
                    except ValueError:
                        acc_list.append(AccountPosition(
                            product=share_acc.product, date=date, account_name='其他应收款', institution='业绩报酬',
                            security_code=pos.security_code, security_name=pos.security_name,
                            volume=abs(flow.trade_amount),
                            currency_origin=share_acc.currency, currency=share_acc.currency,
                        ))
            else:
                raise NotImplementedError('{} {} \n {}'.format(flow.trade_class, len(flow.trade_class), flow))

        acc_list.append(share_acc)

    return acc_list


def separate_inner_bank_flow(data_list: List, product_range: tuple):
    """
    银行流水中的内部交易分解成对应产品的各自流水
    :return: List
    """
    from jetend.jmSheets import BankFlow
    sub_data_list = List()

    for obj in data_list:
        assert isinstance(obj, BankFlow)
        if is_valid_str(obj.extra_info):
            assert obj.extra_info == '内部', obj.__dict__
            if obj.trade_class == '申购':
                sub_data_list.append(BankFlow(
                    product=obj.opposite, date=obj.date, institution='-',
                    trade_class='基金投资', opposite='久铭', subject=obj.product,
                    trade_amount=-abs(obj.trade_amount),
                ))
            elif obj.trade_class == '赎回':
                sub_data_list.append(BankFlow(
                    product=obj.opposite, date=obj.date, institution='-',
                    trade_class='基金投资', opposite='久铭', subject=obj.product,
                    trade_amount=abs(obj.trade_amount),
                ))
            elif obj.trade_class in ('份额转换',):
                sub_data_list.append(BankFlow(
                    product=obj.opposite, date=obj.date, institution='-', trade_class='份额转换',
                    opposite=obj.product, trade_amount=-obj.trade_amount,
                ))
            elif obj.trade_class in ('份额转换差额',):
                sub_data_list.append(BankFlow(
                    product=obj.opposite, date=obj.date, institution='-', trade_class='份额转换差额',
                    opposite=obj.product, trade_amount=-obj.trade_amount,
                ))
            elif obj.trade_class in ('托管户互转',):
                pass
            elif obj.product not in product_range and obj.opposite not in product_range:
                continue
            elif obj.trade_class == '基金转出':
                assert obj.trade_amount < 0, obj.__dict__
                assert obj.opposite in product_range, obj.__dict__
                sub_data_list.append(BankFlow(
                    product=obj.opposite, date=obj.date, institution='-', trade_class='基金转入',
                    opposite=obj.product, trade_amount=-obj.trade_amount,
                ))
            else:
                raise NotImplementedError(obj.__dict__)
        else:
            pass
    return sub_data_list


def update_bank_account_by_bank_flow(last_acc_pos: List, acc_pos: List, bank_flow_list: List, date: datetime.date):
    """
    处理银行流水得到银行余额，生成当日银行余额数据
        * 根据前日银行余额和银行流水计算今日银行余额
    :return: None
    """
    from jetend.jmSheets import BankFlow
    acc_list = List()
    product_processed_set = set()
    # TODO: 对新产品初始化新建银行余额，未完成
    assert bank_flow_list.collect_attr_set('product').issubset(acc_pos.collect_attr_set('product'))

    for bank_acc in acc_pos.find_value_where(account_name='银行存款'):
        assert isinstance(bank_acc, AccountPosition)

        # 检查银行余额的合法性
        assert bank_acc.product not in product_processed_set, '产品{}出现两个银行账户{}'.format(
            bank_acc.product, acc_pos.find_value_where(product=bank_acc.product)
        )  # 默认每个产品只有一个银行账户，不允许产品存在两个银行账户
        product_processed_set.add(bank_acc.product)
        assert date == bank_acc.date, '当日日期{}落后于前一日日期{}'.format(date, bank_acc)
        assert bank_acc.account_name == '银行存款', '未知类型对象{}'.format(bank_acc)

        # 更新银行余额
        for flow in bank_flow_list.find_value_where(product=bank_acc.product):
            assert isinstance(flow, BankFlow)
            assert flow.date == date, '非当日银行流水 {} {}'.format(date, flow)
            if bank_acc.institution == '-' and is_valid_str(flow.institution):  # 消除初始数据不足
                bank_acc.institution = flow.institution
            if bank_acc.institution == '-' or flow.institution == '-':
                pass
            else:
                if bank_acc.institution == flow.institution:
                    pass
                else:
                    continue
                # assert bank_acc.institution == flow.institution, '{}\n{}'.format(flow, bank_acc)

            bank_acc.update_by(flow)
            if flow.trade_class in ('银证转账', '份额转换差额', '增值税及附加',):
                pass
            elif '手续费' in flow.trade_class:
                pass
            elif flow.trade_class in ('新股缴款',):
                acc_obj = AccountPosition(
                    product=flow.product, date=date, account_name='其他应收款', institution='新股',
                    security_code=flow.subject, volume=abs(flow.trade_amount),
                    currency_origin=bank_acc.currency_origin, currency=bank_acc.currency,
                )
                acc_list.append(acc_obj)
            elif flow.trade_class in ('赎回', '基金转出'):  # 消除应付赎回款
                assert flow.trade_amount < 0, str(flow)
                try:
                    acc_obj = acc_pos.find_value(product=bank_acc.product, account_name='应付赎回款',
                                                 institution=flow.opposite, )
                except ValueError:
                    raise RuntimeError('缺少应付赎回款 {}\n{}'.format(
                        flow, acc_pos.find_value_where(account_name='应付赎回款')))
                if abs(abs(acc_obj.volume) - abs(flow.trade_amount)) < 1:
                    acc_obj.volume = 0.0
                else:
                    acc_obj.volume = acc_obj.volume - abs(flow.trade_amount)
                    assert acc_obj.volume > 0, '{}\n{}'.format(acc_obj, flow)
            elif flow.trade_class in ('业绩报酬', '赎回业绩报酬'):
                assert flow.trade_amount < 0, str(flow)
                try:
                    acc_obj = acc_pos.find_value(product=bank_acc.product, account_name='累计已付业绩报酬', )
                    acc_obj.volume = acc_obj.volume + abs(flow.trade_amount)
                except ValueError:
                    acc_obj = AccountPosition(
                        product=flow.product, date=date, account_name='累计已付业绩报酬', institution='久铭',
                        security_code='-', volume=abs(flow.trade_amount),
                        currency_origin=bank_acc.currency_origin, currency=bank_acc.currency,
                    )
                    acc_list.append(acc_obj)
            elif flow.trade_class in ('基金投资',):
                if flow.trade_amount < 0:
                    try:
                        acc_pos.find_value(
                            product=bank_acc.product, account_name='待确认申购款', security_name=flow.subject)
                    except ValueError:
                        raise RuntimeError('申购款划出但缺少待确认申购款 {}\n{}'.format(
                            flow, acc_pos.find_value_where(product=bank_acc.product)))
                    if flow.opposite == '久铭':
                        try:
                            acc_pos.find_value(
                                product=flow.subject, account_name='应付申购款', institution=bank_acc.product, )
                        except ValueError:
                            raise RuntimeError('申购款已被划出但接收方但缺少应付申购款 {}\n{}'.format(
                                flow, acc_pos.find_value_where(account_name='应付申购款')))
                    else:
                        # TODO: 后期处理基金投资
                        raise NotImplementedError(flow)

                elif flow.trade_amount > 0:
                    assert flow.opposite == '久铭', str(flow)
                    acc_obj = acc_pos.find_value(
                        product=bank_acc.product, account_name='其他应收款', institution='基金投资',
                        security_name=flow.subject)
                    if abs(flow.trade_amount - acc_obj.volume) < 10:
                        acc_obj.volume = 0
                    else:
                        acc_obj.volume = acc_obj.volume - abs(flow.trade_amount)
                        assert acc_obj.volume > 0, '{}\n{}'.format(acc_obj, flow)
                        # raise NotImplementedError('{}\n{}'.format(acc_obj, flow))
                else:
                    raise NotImplementedError(flow)
            elif flow.trade_class in ('申购', '基金转入',):
                try:
                    acc_pos.find_value(
                        product=bank_acc.product, account_name='应付申购款', institution=flow.opposite,
                    )
                except ValueError:
                    raise RuntimeError('申购款已收到但缺少应付申购款 {}\n{}'.format(
                        flow, acc_pos.find_value_where(product=bank_acc.product, )))
                # assert flow.trade_amount > 0, '{}'.format(flow)
                # acc_list.append(AccountPosition(
                #     product=flow.product, date=date, account_name='应付申购款', institution=flow.opposite,
                #     security_code='-', volume=abs(flow.trade_amount),
                #     currency_origin='RMB', currency='RMB',
                # ))
            elif flow.trade_class in ('管理费',):
                acc_obj = acc_pos.find_value(product=bank_acc.product, account_name='已付应付管理费')
                acc_obj.volume = acc_obj.volume + abs(flow.trade_amount)
            elif flow.trade_class in ('管理费返还',):
                try:  # 通过 银行流水中的产品名，标的名和流水类型匹配产品余额持仓表中的记录 wavezhou 20220526
                    acc_obj = acc_pos.find_value(product=bank_acc.product, account_name='已收应收管理费返还',
                                                 security_name=bank_acc.security_name)
                    acc_obj.volume = acc_obj.volume + abs(flow.trade_amount)
                except ValueError:
                    acc_obj = acc_pos.find_value(product=bank_acc.product, account_name='累计应收管理费返还',
                                                 security_name=bank_acc.security_name)
                    acc_obj.volume = acc_obj.volume + abs(flow.trade_amount)
            elif flow.trade_class in ('申购退回款',):
                try:
                    assert flow.trade_amount < 0, str(flow)
                    acc_obj = acc_pos.find_value(
                        product=bank_acc.product, account_name='应付申购款', institution=flow.opposite,
                    )
                    assert abs(acc_obj.volume - abs(flow.trade_amount)) < 100, str(flow)
                    acc_obj.volume = acc_obj.volume + flow.trade_amount
                except ValueError:
                    pass
            elif flow.trade_class in ('利息归本',):
                try:
                    acc_obj = last_acc_pos.find_value(
                        product=bank_acc.product, account_name='应收利息', institution=flow.institution)
                    acc_obj.volume = 0.0
                except ValueError:
                    pass
            elif flow.trade_class in ('业绩报酬返还',):
                try:
                    assert flow.trade_amount > 0, str(flow)
                    acc_obj = acc_pos.find_value(
                        product=bank_acc.product, account_name='其他应收款', institution='业绩报酬',
                    )
                    acc_obj.volume = acc_obj.volume - flow.trade_amount
                except ValueError:
                    raise RuntimeError('业绩报酬返还已收到但缺少应收款 {}\n{}'.format(
                        flow, acc_pos.find_value_where(product=bank_acc.product, )))
            else:
                raise NotImplementedError(flow)
    return acc_list


# def handle_account_payable_receivable_by_bank_flow(last_acc_list: List, bank_flow_list: List, date: datetime.date):
#     from jetend.jmSheets import BankFlow
#
#     result_list = List()
#     for last_acc in last_acc_list:
#         assert isinstance(last_acc, AccountPosition)
#         assert last_acc.account_name in ('其他应付款', ), '{}'.format(last_acc)
#
#         acc = AccountPosition().update(last_acc)
#         acc.date = date
#
#         for flow in bank_flow_list.find_value_where(product=acc.product):
#             assert isinstance(flow, BankFlow)
#             raise NotImplementedError(flow)
#
#         result_list.append(acc)
#
#     return result_list


def handle_security_account_by_bank_flow(last_acc_list: List, bank_flow_list: List, date: datetime.date):
    """
    处理银行流水得到受到银证转账影响的证券账户余额
        * 根据前日账户余额和银行流水计算今日账户余额（没有考虑红利、交易流水）
    :return:
    """
    from jetend.jmSheets import BankFlow

    # TODO: 对新产品新账户初始化账户余额，未完成
    # assert bank_flow_list.collect_attr_set('product').issubset(last_acc_list.collect_attr_set('product')), '{}'.format(
    #     bank_flow_list.collect_attr_set('product') - last_acc_list.collect_attr_set('product')
    # )

    acc_list = List()

    for last_acc in last_acc_list:
        assert isinstance(last_acc, AccountPosition)
        assert date > last_acc.date, '当日日期{}落后于前一日日期{}'.format(date, last_acc)
        assert last_acc.account_name in ('证券账户', '期货账户', '期权账户', '信用账户',), '未知类型对象{}'.format(last_acc)

        acc = AccountPosition().update(last_acc)
        acc.date = date  # 更新账户日期
        acc_list.append(acc)

    for flow in bank_flow_list:
        assert isinstance(flow, BankFlow)
        assert flow.date == date, '非当日银行流水 {} {}'.format(date, flow)
        if '手续费' in flow.trade_class:
            continue
        elif flow.trade_class in (
                '新股缴款', '申购', '利息归本', '赎回', '业绩报酬',
        ):
            continue
        elif flow.trade_class in ('银证转账',):
            try:
                acc = acc_list.find_value(product=flow.product, institution=flow.opposite)
                acc.volume = acc.volume - flow.trade_amount
                assert acc.volume > - 1.0, '{}\n{}'.format(acc, flow)
            except ValueError:
                raise NotImplementedError('\n{}'.format(flow))
        else:
            raise NotImplementedError(flow)

    return acc_list


def handle_security_account_position_by_trade_flow(
        info_board: jmInfoBoard, acc_list: List, last_pos_list: List, date: datetime.date, product_range: tuple,
):
    """
    处理交易流水得到证券账户余额
        * 更新持仓数量
        * 更新证券余额和期货町市
    :return:
    """
    from jetend.Constants import DataBaseName
    from jetend.jmSheets import EstimatedNormalTradeFlow
    new_acc_pos = List()

    for last_pos in last_pos_list:
        assert isinstance(last_pos, AccountPosition)
        assert not last_pos.is_account(), '{}'.format(last_pos.__dict_data__)
        pos = AccountPosition().update(last_pos)
        pos.date = date
        new_acc_pos.append(pos)

    # 当日普通交易流水
    trade_flow_list = List.from_pd(EstimatedNormalTradeFlow, info_board.db.read_pd_query(DataBaseName.management, """
    SELECT * FROM 当日普通交易流水 WHERE 日期 = '{}';""".format(date)))

    for flow in trade_flow_list:
        if flow.product not in product_range:
            continue
        flow.institution = flow.institution.replace('证券', '')

        try:
            acc = acc_list.find_value(product=flow.product, institution=flow.institution)  # 更新账户资金
        except ValueError as v_error:
            print(flow)
            print(acc_list.find_value_where(product=flow.product, ))
            raise v_error
        assert isinstance(acc, AccountPosition)
        acc.update_by(flow)

        try:  # 更新账户持仓
            pos = new_acc_pos.find_value(
                product=flow.product, institution=flow.institution, security_code=flow.security_code,
            )
        except ValueError:
            pos = AccountPosition(
                product=flow.product, date=date, institution=flow.institution, security_code=flow.security_code,
                account_name=info_board.find_security_type_by_code(flow.security_code),
                security_name=info_board.find_security_name_by_code(flow.security_code),
                volume=0.0, currency_origin=acc.currency_origin, currency=acc.currency,
            )
            new_acc_pos.append(pos)
        assert isinstance(pos, AccountPosition)
        pos.update_by(flow)

    # 当日两融交易流水
    trade_flow_list = List.from_pd(EstimatedNormalTradeFlow, info_board.db.read_pd_query(DataBaseName.management, """
    SELECT * FROM 当日两融交易流水 WHERE 日期 = '{}';""".format(date)))

    for flow in trade_flow_list:
        if flow.product not in product_range:
            continue

        acc = acc_list.find_value(product=flow.product, institution=flow.institution)  # 更新账户资金
        assert isinstance(acc, AccountPosition)
        acc.update_by(flow)

        try:  # 更新账户持仓
            pos = new_acc_pos.find_value(
                product=flow.product, institution=flow.institution, security_code=flow.security_code,
            )
        except ValueError:
            pos = AccountPosition(
                product=flow.product, date=date, institution=flow.institution, security_code=flow.security_code,
                account_name=info_board.find_security_type_by_code(flow.security_code),
                security_name=info_board.find_security_name_by_code(flow.security_code),
                volume=0.0, currency_origin=acc.currency_origin, currency=acc.currency,
            )
            new_acc_pos.append(pos)
        assert isinstance(pos, AccountPosition)
        pos.update_by(flow)

    # 当日期货交易流水
    trade_flow_list = List.from_pd(EstimatedNormalTradeFlow, info_board.db.read_pd_query(DataBaseName.management, """
    SELECT * FROM 当日期货交易流水 WHERE 日期 = '{}';""".format(date)))

    for flow in trade_flow_list:
        if flow.product not in product_range:
            continue

        acc = acc_list.find_value(product=flow.product, institution=flow.institution)  # 更新账户资金
        assert isinstance(acc, AccountPosition)
        acc.update_by(flow)

        try:  # 更新账户持仓
            pos = new_acc_pos.find_value(
                product=flow.product, institution=flow.institution, security_code=flow.security_code,
            )
        except ValueError:
            pos = AccountPosition(
                product=flow.product, date=date, institution=flow.institution, security_code=flow.security_code,
                account_name=info_board.find_security_type_by_code(flow.security_code),
                security_name=info_board.find_security_name_by_code(flow.security_code),
                volume=0.0, currency_origin=acc.currency_origin, currency=acc.currency,
            )
            new_acc_pos.append(pos)
        assert isinstance(pos, AccountPosition)
        pos.update_by(flow)

    return new_acc_pos


def handle_security_account(
        info_board: jmInfoBoard, last_acc_pos: List, current_date: datetime.date,
        product_range: tuple,
):
    from jetend.Constants import DataBaseName
    from jetend.jmSheets import RawNormalAccount, RawMarginAccount, RawFutureAccount, RawOptionAccount

    # TODO: 检查 last_acc_pos 中存在但读取的对账单中不存在的账户余额
    acc_pos_list = List()

    # ------------- [证券账户] ------------- #
    normal_acc_list = List.from_pd(RawNormalAccount, info_board.db.read_pd_query(
        DataBaseName.management,
        """SELECT * FROM `原始普通账户资金记录` WHERE `日期` = (
            SELECT MAX(日期) FROM `原始普通账户资金记录` WHERE `日期` <= '{}'
        );""".format(current_date)
    ))
    # product_range = normal_acc_list.collect_attr_set('product')
    # product_range.update(last_acc_pos.find_value_where(account_name='证券账户').collect_attr_set('product'))
    for product in product_range:
        institution_range = normal_acc_list.find_value_where(product=product).collect_attr_set('institution')
        institution_range.update(last_acc_pos.find_value_where(
            account_name='证券账户', product=product
        ).collect_attr_set('institution'))
        for institution in institution_range:
            if '收益互换' in institution or institution in ('华泰互换',):
                continue
            # if '申万' in institution or institution in ('申万',):
            #     continue
            if product == '久铭2号' and institution == '国君':
                continue
            if product == '稳健18号' and institution == '国君':
                continue
            if product == '稳健12号' and institution == '中信':
                continue
            if product == '稳健19号' and institution == '中信':
                continue
            if product == '稳健18号' and institution == '财通':
                continue
            try:
                acc = normal_acc_list.find_value(product=product, institution=institution)
                acc_pos_list.append(AccountPosition(
                    product=acc.product, date=current_date, account_name='证券账户', institution=acc.institution,
                    security_code='-', volume=acc.cash_amount, currency_origin='RMB', currency='RMB',
                ))
            except ValueError:
                if info_board.is_active_normal_account(product, institution, current_date):
                    raise RuntimeError('遗漏普通账户对账单 {} {} {}'.format(product, institution, current_date))
                try:
                    acc = last_acc_pos.find_value(product=product, account_name='证券账户', institution=institution)
                    new_acc = AccountPosition().update(acc)
                    new_acc.date = current_date
                    acc_pos_list.append(new_acc)
                except ValueError:
                    raise RuntimeError('遗漏普通账户资金信息 {} {} {}\n{}'.format(
                        product, institution, current_date, last_acc_pos.find_value_where(product=product)))

    margin_acc_list = List.from_pd(RawMarginAccount, info_board.db.read_pd_query(
        DataBaseName.management,
        """SELECT * FROM `原始两融账户资金记录` WHERE `日期` = (
            SELECT MAX(日期) FROM `原始两融账户资金记录` WHERE `日期` <= '{}'
        );""".format(current_date)
    ))
    # product_range = margin_acc_list.collect_attr_set('product')
    # product_range.update(last_acc_pos.find_value_where(account_name='信用账户').collect_attr_set('product'))
    # from core.Valuation import ManagementProducts
    for product in product_range:
        # if product not in ManagementProducts:
        #     continue
        institution_range = margin_acc_list.find_value_where(product=product).collect_attr_set('institution')
        institution_range.update(last_acc_pos.find_value_where(
            account_name='信用账户', product=product
        ).collect_attr_set('institution'))
        for institution in institution_range:
            if product == '稳健12号' and institution == '中信两融':
                continue
            if product == '稳健19号' and institution == '中信两融':
                continue
            try:
                acc = margin_acc_list.find_value(product=product, institution=institution)
                acc_pos_list.append(AccountPosition(
                    product=acc.product, date=current_date, account_name='信用账户', institution=acc.institution,
                    security_code='-', volume=acc.cash_amount, currency_origin='RMB', currency='RMB',
                ))
                if abs(acc.liability_principal) > 0.0:
                    acc_pos_list.append(AccountPosition(
                        product=acc.product, date=current_date, account_name='短期借款', institution=acc.institution,
                        security_code='-', volume=abs(acc.liability_principal), currency_origin='RMB', currency='RMB',
                    ))
                liability_amount_for_pay = acc.liability_amount_for_pay
                if not is_valid_float(liability_amount_for_pay):
                    liability_amount_for_pay = 0.0
                if abs(abs(acc.liability_amount_interest) + abs(liability_amount_for_pay)) > 0.0:
                    if acc.date == current_date:
                        acc_pos_list.append(AccountPosition(
                            product=acc.product, date=current_date, account_name='应付融资利息',
                            institution=acc.institution, security_code='-',
                            volume=abs(acc.liability_amount_interest) + abs(liability_amount_for_pay),
                            currency_origin='RMB', currency='RMB',
                        ))
                    elif acc.date < current_date:
                        date_gap = (current_date - acc.date) / datetime.timedelta(days=1)
                        rate = info_board.find_product_account_interest_rate(
                            acc.product, '融资账户', acc.institution, current_date)
                        interest_amount = abs(acc.liability_amount_interest) + abs(liability_amount_for_pay)
                        if acc.institution in ('中信两融', '招商两融', '德邦两融'):  # 按日计提
                            interest_amount += (abs(acc.liability_principal) + abs(
                                acc.liability_amount_fee)) * rate.interest_rate * date_gap / rate.yearly_accrued_days
                        elif acc.institution in ('长江两融', '安信两融'):  # 周五一次性计提
                            pass
                        else:
                            if acc.product == '久铭9号':
                                pass
                            else:
                                raise NotImplementedError(acc)
                        acc_pos_list.append(AccountPosition(
                            product=acc.product, date=current_date, account_name='应付融资利息',
                            institution=acc.institution, security_code='-', volume=interest_amount,
                            currency_origin='RMB', currency='RMB',
                        ))
                    else:
                        raise RuntimeError('{} {} {}\n{}'.format(product, institution, current_date, acc))
                if abs(acc.liability_amount_fee) > 0.0:
                    acc_pos_list.append(AccountPosition(
                        product=acc.product, date=current_date, account_name='应付融资费用', institution=acc.institution,
                        security_code='-', volume=abs(acc.liability_amount_fee),
                        currency_origin='RMB', currency='RMB',
                    ))
            except ValueError:
                if info_board.is_active_margin_account(product, institution, current_date):
                    raise RuntimeError('遗漏两融账户对账单 {} {} {}'.format(product, institution, current_date))
                try:
                    acc = last_acc_pos.find_value(product=product, account_name='信用账户', institution=institution)
                    new_acc = AccountPosition().update(acc)
                    new_acc.date = current_date
                    acc_pos_list.append(new_acc)
                except ValueError:
                    raise RuntimeError('遗漏两融账户资金信息 {} {} {}\n{}'.format(
                        product, institution, current_date, last_acc_pos.find_value_where(product=product)))

    future_acc_list = List.from_pd(RawFutureAccount, info_board.db.read_pd_query(
        DataBaseName.management,
        """SELECT * FROM `原始期货账户资金记录` WHERE `日期` = (
            SELECT MAX(日期) FROM `原始期货账户资金记录` WHERE `日期` <= '{}'
        );""".format(current_date)
    ))
    for product in product_range:
        institution_range = future_acc_list.find_value_where(product=product).collect_attr_set('institution')
        institution_range.update(last_acc_pos.find_value_where(
            account_name='期货账户', product=product
        ).collect_attr_set('institution'))
        for institution in institution_range:
            try:
                acc = future_acc_list.find_value(product=product, institution=institution)
                acc_pos_list.append(AccountPosition(
                    product=acc.product, date=current_date, account_name='期货账户', institution=acc.institution,
                    security_code='-', volume=acc.capital_sum, currency_origin='RMB', currency='RMB',
                ))
            except ValueError:
                if info_board.is_active_future_account(product, institution, current_date):
                    if info_board.check_mandatory(product) is True:
                        raise RuntimeError('遗漏期货账户对账单 {} {} {}'.format(product, institution, current_date))
                    else:
                        pass
                try:
                    acc = last_acc_pos.find_value(product=product, account_name='期货账户', institution=institution)
                    new_acc = AccountPosition().update(acc)
                    new_acc.date = current_date
                    acc_pos_list.append(new_acc)
                except ValueError:
                    raise RuntimeError('遗漏期货账户资金信息 {} {} {}\n{}'.format(
                        product, institution, current_date, last_acc_pos.find_value_where(product=product)))

    # TODO: 检查期权账户资金
    option_acc_list = List.from_pd(RawOptionAccount, info_board.db.read_pd_query(
        DataBaseName.management,
        """SELECT * FROM `原始期权账户资金记录` WHERE `日期` = (
            SELECT MAX(日期) FROM `原始期权账户资金记录` WHERE `日期` <= '{}'
        );""".format(current_date)
    ))
    for product in product_range:
        institution_range = option_acc_list.find_value_where(product=product).collect_attr_set('institution')
        institution_range.update(last_acc_pos.find_value_where(
            account_name='期权账户', product=product
        ).collect_attr_set('institution'))
        for institution in institution_range:
            try:
                acc = option_acc_list.find_value(product=product, institution=institution)
                acc_pos_list.append(AccountPosition(
                    product=acc.product, date=current_date, account_name='期权账户', institution=acc.institution,
                    security_code='-', volume=acc.cash_amount, currency_origin='RMB', currency='RMB',
                ))
            except ValueError:
                if info_board.is_active_future_account(product, institution, current_date):
                    if info_board.check_mandatory(product) is True:
                        raise RuntimeError('遗漏期权账户对账单 {} {} {}'.format(product, institution, current_date))
                    else:
                        pass
                try:
                    acc = last_acc_pos.find_value(product=product, account_name='期权账户', institution=institution)
                    new_acc = AccountPosition().update(acc)
                    new_acc.date = current_date
                    acc_pos_list.append(new_acc)
                except ValueError:
                    raise RuntimeError('遗漏期权账户资金信息 {} {} {}\n{}'.format(
                        product, institution, current_date, last_acc_pos.find_value_where(product=product)))

    return acc_pos_list


def handle_security_position(
        info_board: jmInfoBoard, last_acc_pos: List, current_date: datetime.date,
        product_range: tuple,
):
    from jetend.Constants import DataBaseName
    from jetend.jmSheets import RawNormalPosition, RawMarginPosition, RawOptionPosition
    acc_pos_list = List()
    normal_pos_list = List.from_pd(RawNormalPosition, info_board.db.read_pd_query(DataBaseName.management, """
    SELECT * FROM `原始普通持仓记录` WHERE `日期` = (SELECT MAX(日期) FROM `原始普通持仓记录` WHERE `日期` <= '{}')
    ;""".format(current_date)))
    position_date = normal_pos_list.collect_attr_set('date')
    assert len(position_date) == 1, normal_pos_list
    position_date = list(position_date)[0]
    for pos in normal_pos_list:
        try:
            security_type = info_board.find_security_type_by_code(pos.security_code)
        except RuntimeError:
            if pos.product not in product_range:
                continue
            else:
                raise RuntimeError('证券代码规整表找不到 {}'.format(pos))
        security_name = info_board.find_security_name_by_code(pos.security_code)
        if 'HK' in pos.security_code.upper():
            currency_origin = 'HKD'
        else:
            currency_origin = 'RMB'
        acc_pos_list.append(AccountPosition(
            product=pos.product, date=current_date, account_name=security_type, institution=pos.institution,
            security_code=pos.security_code, security_name=security_name, volume=pos.hold_volume,
            currency_origin=currency_origin, currency='RMB', raw_market_value=pos.market_value,
        ))
    # margin_pos_list = List.from_pd(RawMarginPosition, info_board.db.read_pd_query(
    #     DataBaseName.management,
    #     """SELECT * FROM `原始两融持仓记录` WHERE `日期` = (
    #         SELECT MAX(日期) FROM `原始两融持仓记录` WHERE `日期` <= '{}'
    #     );""".format(current_date)
    # ))
    margin_pos_list = List.from_pd(RawMarginPosition, info_board.db.read_pd_query(
        DataBaseName.management,
        """SELECT * FROM `原始两融持仓记录` WHERE `日期` = '{}';""".format(position_date)
    ))
    for pos in margin_pos_list:
        try:
            security_type = info_board.find_security_type_by_code(pos.security_code)
        except RuntimeError:
            if pos.product not in product_range:
                continue
            else:
                raise RuntimeError('证券代码规整表找不到 {}'.format(pos))
        security_name = info_board.find_security_name_by_code(pos.security_code)
        if 'HK' in pos.security_code.upper():
            currency_origin = 'HKD'
        else:
            currency_origin = 'RMB'
        acc_pos_list.append(AccountPosition(
            product=pos.product, date=current_date, account_name=security_type, institution=pos.institution,
            security_code=pos.security_code, security_name=security_name, volume=pos.hold_volume,
            currency_origin=currency_origin, currency='RMB',
        ))
    option_pos_list = List.from_pd(RawOptionPosition, info_board.db.read_pd_query(
        DataBaseName.management,
        """SELECT * FROM `原始期权持仓记录` WHERE `日期` = '{}';""".format(position_date)
    ))
    for pos in option_pos_list:
        security_type = '期权'
        # security_name = info_board.find_security_name_by_code(pos.security_code)
        if 'HK' in pos.security_code.upper():
            currency_origin = 'HKD'
        else:
            currency_origin = 'RMB'
        acc_pos_list.append(AccountPosition(
            product=pos.product, date=current_date, account_name=security_type, institution=pos.institution,
            security_code=pos.security_code, security_name=pos.security_name, volume=pos.hold_volume,
            market_value=pos.market_value,
            currency_origin=currency_origin, currency='RMB',
        ))
    # future_pos_list = List.from_pd(RawFuturePosition, info_board.db.read_pd_query(
    #     DataBaseName.management,
    #     """SELECT * FROM `原始期货持仓记录` WHERE `日期` = (
    #         SELECT MAX(日期) FROM `原始期货持仓记录` WHERE `日期` <= '{}'
    #     );""".format(current_date)
    # ))
    # future_pos_list = List.from_pd(RawFuturePosition, info_board.db.read_pd_query(
    #     DataBaseName.management,
    #     """SELECT * FROM `原始期货持仓记录` WHERE `日期` = '{}';""".format(position_date)
    # ))
    # for pos in future_pos_list:
    #     # if pos.date - current_date < datetime.timedelta(days=30):
    #     #     continue
    #     if pos.product not in product_range:
    #         continue
    #     # try:
    #     #     security_type = info_board.find_security_type_by_code(pos.security_code)
    #     # except RuntimeError:
    #     #     # raise RuntimeError('证券代码规整表找不到 {}'.format(pos))
    #     security_type = '期货'
    #     security_name = pos.security_code
    #     # security_name = info_board.find_security_name_by_code(pos.security_code)
    #     acc_pos_list.append(AccountPosition(
    #         product=pos.product, date=current_date, account_name=security_type, institution=pos.institution,
    #         security_code=pos.security_code, security_name=security_name, volume=pos.hold_volume,
    #         market_value=pos.margin, currency_origin='RMB', currency='RMB',
    #     ))
    #     # inner2outer_map = {
    #     #     'product': '产品', 'date': '日期', 'account_name': '科目名称', 'institution': '机构',
    #     #     'security_code': '证券代码', 'security_name': '证券名称',
    #     #     'volume': '数量', 'market_price_origin': '原始市场价', 'currency_origin': '原始货币',
    #     #     'exchange_rate': '汇率', 'market_price': '市场价', 'market_value': '市值', 'currency': '货币',
    #     # }

    return acc_pos_list


def handle_bond_interest_receivable(pos_list: List, date: datetime.date, product_range: tuple):
    """
    处理债券应收利息
        * 债券利息提计
    :return:
    """
    from modules.Modules import Modules

    env = Modules.get_instance()
    acc_list = List()

    for pos in pos_list:
        assert isinstance(pos, AccountPosition)
        if pos.product not in product_range:
            continue
        if '债' not in pos.account_name:
            continue
        # TODO: 后续付息日需要单独转出待收利息
        assert pos.date == date, '日期不匹配 {}\n{}'.format(date, pos)
        on_day_rate = env.market_board.float_field('self.accruedinterest', pos.security_code, pos.date)
        last_day_rate = env.market_board.float_field(
            'self.accruedinterest', pos.security_code, pos.date - datetime.timedelta(days=1),
        )
        assert on_day_rate > last_day_rate, str(pos)
        acc_list.append(AccountPosition(
            product=pos.product, date=date, account_name='应收债券利息', institution=pos.institution,
            security_code=pos.security_code, security_name=pos.security_name,
            volume=pos.volume * on_day_rate,
            currency_origin=pos.currency_origin, currency=pos.currency,
        ))

    return acc_list


swap_institution_map = {
    '中信美股': '美股收益互换', '中信港股': '港股收益互换',
}


def handle_htsc_swap_account_position(info_board: jmInfoBoard, last_acc_pos: List, current_date: datetime.date):
    from jetend.jmSheets import RawSwapHtscAccount, RawSwapHtscPosition
    from jetend.Constants import DataBaseName
    acc_pos_list = List()

    swap_acc_list = List.from_pd(RawSwapHtscAccount, info_board.db.read_pd_query(
        DataBaseName.management,
        """
        SELECT * FROM `原始华泰收益互换账户资金记录` 
        WHERE `日期` = (SELECT MAX(日期) FROM `原始华泰收益互换账户资金记录` WHERE `日期` <= '{}');
        """.format(current_date),
    ))
    swap_date = list(swap_acc_list.collect_attr_set('date'))
    assert len(swap_date) == 1, str(swap_date)
    swap_date = swap_date[0]
    assert isinstance(swap_date, datetime.date), swap_date
    currency_change_rate_map = dict()
    for currency in ('US', 'HK'):
        currency_change_rate_map[currency] = list(
            swap_acc_list.find_value_where(trade_market=currency).collect_attr_set('exchange_rate')
        )[0]
    swap_pos_list = List.from_pd(RawSwapHtscPosition, info_board.db.read_pd_query(
        DataBaseName.management,
        """
        SELECT * FROM `原始华泰收益互换持仓记录` 
        WHERE `日期` = (SELECT MAX(日期) FROM `原始华泰收益互换持仓记录` WHERE `日期` <= '{}');
        """.format(current_date),
    ))
    assert list(swap_pos_list.collect_attr_set('date'))[0] == swap_date, '{}\n{}'.format(swap_date, swap_pos_list)

    swap_product_range = last_acc_pos.collect_attr_set('product')
    swap_product_range.update(swap_pos_list.collect_attr_set('product'))

    for product in swap_product_range:
        institution = '华泰互换'
        institution_str = institution
        # if len(last_acc_pos.find_value_where(product=product, institution=institution)) == 0 and len(
        #     swap_acc_list.find_value_where(product=product, institution=institution_str)
        # ) == 0:
        #     continue
        swap_acc = swap_acc_list.find_value(product=product, trade_market='合计')
        if current_date >= swap_date:
            acc_pos_list.append(AccountPosition(
                product=product, date=current_date, account_name='证券账户', institution=institution,
                security_code='-', currency_origin='RMB', currency='RMB',
                volume=swap_acc.margin_balance - swap_acc.long_position_principle
            ))
            acc_pos_list.append(AccountPosition(
                product=product, date=current_date, account_name='应付利息', institution=institution,
                security_code='-', currency_origin='RMB', currency='RMB',
                volume=abs(swap_acc.long_accumulated_interest_payable)
            ))
        # elif current_date > swap_date:
        #     date_gap = int((current_date - swap_date) / datetime.timedelta(days=1))
        #     acc_pos_list.append(AccountPosition(
        #         product=product, date=current_date, account_name='证券账户', institution=institution,
        #         security_code='-', currency_origin=swap_acc.currency, currency='RMB',
        #         volume=swap_acc.available_balance,
        #     ))
        #     obj = abs(swap_acc.accumulated_interest_accrued - swap_acc.accumulated_interest_payed)
        #     obj += swap_acc.notional_principle_origin * 0.015 * date_gap / 365
        #     if swap_acc.available_balance < 0:
        #         obj += abs(swap_acc.available_balance) * 0.07 * date_gap / 365
        #     if swap_acc.notional_principle_origin - swap_acc.prepaid_balance_origin > 0:
        #         obj += 0.07 * date_gap * (
        #                 swap_acc.notional_principle_origin - swap_acc.prepaid_balance_origin
        #         ) / 365
        #     acc_pos_list.append(AccountPosition(
        #         product=product, date=current_date, account_name='应付利息', institution=institution,
        #         security_code='-', currency_origin=swap_acc.currency, currency='RMB', volume=obj,
        #     ))
        else:
            raise NotImplementedError('{} {}'.format(current_date, swap_date))
        for pos in swap_pos_list.find_value_where(product=product, institution=institution_str):
            if abs(pos.hold_volume) < 0.01:
                continue
            acc_pos_list.append(AccountPosition(
                product=product, date=current_date, account_name='股票', institution=institution,
                security_code=pos.security_code,  # security_name=pos.security_name,
                volume=pos.hold_volume, exchange_rate=currency_change_rate_map[pos.trade_market],
                currency_origin=swap_acc.trade_currency, currency='RMB',
                market_price_origin=pos.close_price,
            ))
    # assert len(swap_pos_list) == len(acc_pos_list.find_value_where(account_name='股票')), '{}\n{}\n{}'.format(
    #     current_date, swap_pos_list, acc_pos_list)
    return acc_pos_list


def handle_citic_swap_account_position(info_board: jmInfoBoard, last_acc_pos: List, current_date: datetime.date):
    from jetend.jmSheets import RawSwapCiticAccount, RawSwapCiticPosition
    from jetend.Constants import DataBaseName
    acc_pos_list = List()

    swap_acc_list = List.from_pd(RawSwapCiticAccount, info_board.db.read_pd_query(
        DataBaseName.management,
        """
        SELECT * FROM `原始中信收益互换账户资金记录` 
        WHERE `日期` = (SELECT MAX(日期) FROM `原始中信收益互换账户资金记录` WHERE `日期` <= '{}');
        """.format(current_date),
    ))
    swap_date = list(swap_acc_list.collect_attr_set('date'))
    assert len(swap_date) == 1, str(swap_date)
    swap_date = swap_date[0]
    assert isinstance(swap_date, datetime.date), swap_date
    swap_pos_list = List.from_pd(RawSwapCiticPosition, info_board.db.read_pd_query(
        DataBaseName.management,
        """
        SELECT * FROM `原始中信收益互换持仓记录` 
        WHERE `日期` = (SELECT MAX(日期) FROM `原始中信收益互换持仓记录` WHERE `日期` <= '{}');
        """.format(current_date),
    ))
    # assert list(swap_pos_list.collect_attr_set('date'))[0] == swap_date, '{}\n{}'.format(swap_date, swap_pos_list)

    swap_product_range = last_acc_pos.collect_attr_set('product')
    swap_product_range.update(swap_pos_list.collect_attr_set('product'))

    for product in swap_product_range:
        for institution in ('美股收益互换', '港股收益互换'):
            if institution == '美股收益互换':
                institution_str = '中信美股'
            elif institution == '港股收益互换':
                institution_str = '中信港股'
            else:
                raise NotImplementedError(institution)
            if len(last_acc_pos.find_value_where(product=product, institution=institution)) == 0 and len(
                    swap_acc_list.find_value_where(product=product, institution=institution_str)
            ) == 0:
                continue
            swap_acc = swap_acc_list.find_value(product=product, institution=institution_str)
            # if current_date == swap_date:
            # assert abs(swap_acc.accumulated_interest_accrued) >= abs(swap_acc.accumulated_interest_payed), swap_acc
            if current_date >= swap_date:
                acc_pos_list.append(AccountPosition(
                    product=product, date=current_date, account_name='证券账户', institution=institution,
                    security_code='-', currency_origin=swap_acc.currency, currency='RMB',
                    volume=swap_acc.accumulated_withdrawal / swap_acc.exchange_rate
                           + swap_acc.carryover_balance_origin - swap_acc.initial_margin_origin
                ))
                acc_pos_list.append(AccountPosition(
                    product=product, date=current_date, account_name='应付利息', institution=institution,
                    security_code='-', currency_origin=swap_acc.currency, currency='RMB',
                    volume=abs(swap_acc.accumulated_interest_accrued) - abs(swap_acc.accumulated_interest_payed)
                ))
            # elif current_date > swap_date:
            #     date_gap = int((current_date - swap_date) / datetime.timedelta(days=1))
            #     acc_pos_list.append(AccountPosition(
            #         product=product, date=current_date, account_name='证券账户', institution=institution,
            #         security_code='-', currency_origin=swap_acc.currency, currency='RMB',
            #         volume=swap_acc.available_balance,
            #     ))
            #     obj = abs(swap_acc.accumulated_interest_accrued - swap_acc.accumulated_interest_payed)
            #     obj += swap_acc.notional_principle_origin * 0.015 * date_gap / 365
            #     if swap_acc.available_balance < 0:
            #         obj += abs(swap_acc.available_balance) * 0.07 * date_gap / 365
            #     if swap_acc.notional_principle_origin - swap_acc.prepaid_balance_origin > 0:
            #         obj += 0.07 * date_gap * (
            #                 swap_acc.notional_principle_origin - swap_acc.prepaid_balance_origin
            #         ) / 365
            #     acc_pos_list.append(AccountPosition(
            #         product=product, date=current_date, account_name='应付利息', institution=institution,
            #         security_code='-', currency_origin=swap_acc.currency, currency='RMB', volume=obj,
            #     ))
            else:
                raise NotImplementedError('{} {}'.format(current_date, swap_date))
            for pos in swap_pos_list.find_value_where(product=product, institution=institution_str):
                if abs(pos.hold_volume) < 0.01:
                    continue
                acc_pos_list.append(AccountPosition(
                    product=product, date=current_date, account_name='股票', institution=institution,
                    security_code=pos.security_code, security_name=pos.security_name,
                    volume=pos.hold_volume, exchange_rate=swap_acc.exchange_rate,
                    currency_origin=swap_acc.currency, currency='RMB',
                ))
    # assert len(swap_pos_list) == len(acc_pos_list.find_value_where(account_name='股票')), '{}\n{}\n{}'.format(
    #     current_date, swap_pos_list, acc_pos_list)
    return acc_pos_list


# def handle_swap_accounts(currency_origin: str, swap_loaded: dict, date: datetime.date, ):
#
#     result_list = List()
#
#     institution_tag = {'USD': '美股收益互换', 'HKD': '港股收益互换'}[currency_origin]
#
#     if swap_loaded['loaded_date'] == date:
#         for product in swap_loaded.keys():
#             if not isinstance(swap_loaded[product], list):
#                 continue
#             balance_dict, underlying_list, calculation_dict = swap_loaded[product]
#             # 计算账户余额
#             assert is_valid_float(balance_dict['accumulated_withdrawal']), '{}'.format(balance_dict)         # 累计支取预付金
#             assert is_valid_float(balance_dict['carryover_balance_origin']), '{}'.format(balance_dict)      # 结转预付金
#             assert is_valid_float(calculation_dict['initial_margin_origin']), '{}'.format(calculation_dict)  # 标的成本
#             obj = float_check(balance_dict['accumulated_withdrawal']) / float_check(swap_loaded['exchange_rate']) \
#                 + float_check(balance_dict['carryover_balance_origin']) \
#                 - float_check(calculation_dict['initial_margin_origin'])
#             result_list.append(AccountPosition(
#                 product=product, date=date, account_name='证券账户', institution=institution_tag,
#                 security_code='-', volume=obj, currency_origin=currency_origin, currency='RMB',
#             ))
#             # 计算应付利息
#             assert is_valid_float(calculation_dict['accumulated_interest_accrued']), '{}'.format(calculation_dict)
#             assert is_valid_float(calculation_dict['accumulated_interest_payed']), '{}'.format(calculation_dict)
#             obj = abs(float_check(calculation_dict['accumulated_interest_accrued'])) - abs(
#                 float_check(calculation_dict['accumulated_interest_payed']))
#             result_list.append(AccountPosition(
#                 product=product, date=date, account_name='应付利息', institution=institution_tag,
#                 security_code='-', volume=obj, currency_origin=currency_origin, currency='RMB',
#             ))
#             print(result_list[-1])
#
#     elif swap_loaded['loaded_date'] < date:
#         days_passed = (date - swap_loaded['loaded_date']) / datetime.timedelta(days=1)
#         for product in swap_loaded.keys():
#             if not isinstance(swap_loaded[product], list):
#                 continue
#             balance_dict, underlying_list, calculation_dict = swap_loaded[product]
#             # 计算账户余额
#             assert is_valid_float(balance_dict['available_balance']), '{}'.format(balance_dict)  # 保证金余额
#             obj = float_check(balance_dict['available_balance'])
#             result_list.append(AccountPosition(
#                 product=product, date=date, account_name='证券账户', institution=institution_tag,
#                 security_code='-', volume=obj, currency_origin=currency_origin, currency='RMB',
#             ))
#             # 计算应付利息
#             assert is_valid_float(calculation_dict['notional_principle_origin']), '{}'.format(calculation_dict)  # 名义本金 - 成本
#             assert is_valid_float(balance_dict['total_balance']), '{}'.format(balance_dict)   # 预付金余额
#             assert is_valid_float(calculation_dict['accumulated_interest_accrued']), '{}'.format(calculation_dict)
#             assert is_valid_float(calculation_dict['accumulated_interest_payed']), '{}'.format(calculation_dict)
#             obj = abs(float_check(calculation_dict['accumulated_interest_accrued'])) - abs(
#                 float_check(calculation_dict['accumulated_interest_payed']))
#             # obj = abs(obj)
#             obj += float_check(calculation_dict['notional_principle_origin']) * 0.015 * days_passed / 365
#             if float_check(balance_dict['available_balance']) < 0:
#                 obj += abs(float_check(balance_dict['available_balance'])) * 0.07 * days_passed / 365
#             gap = float_check(calculation_dict['notional_principle_origin']) \
#                 - float_check(balance_dict['total_balance'])
#             if gap > 0:
#                 obj += gap * 0.07 * days_passed / 365
#             result_list.append(AccountPosition(
#                 product=product, date=date, account_name='应付利息', institution=institution_tag,
#                 security_code='-', volume=obj, currency_origin=currency_origin, currency='RMB',
#             ))
#             print(result_list[-1])
#
#     else:
#         raise RuntimeError('{} {}'.format(swap_loaded['loaded_date'], date))
#     return result_list


def handle_product_mandate_fee_payable(
        info_board: jmInfoBoard, acc_pos: List, date: datetime.date
):
    """
    处理当日托管相关费用
    :return:
    """
    from jetend.Constants import DataBaseName
    from jetend.jmSheets import RawTrusteeshipValuation
    # result_list = List()

    value_states = List.from_pd(RawTrusteeshipValuation, info_board.db.read_pd_query(
        DataBaseName.management,
        """
        SELECT * FROM `原始托管估值表净值表` 
        WHERE `日期` = (SELECT MAX(日期) FROM `原始托管估值表净值表` WHERE `日期` < '{}')
        ;""".format(date)
    ))

    for obj in acc_pos:
        if obj.institution == '托管费':
            fee_rate = info_board.find_product_mandate_fee_rate(obj.product, date)
        elif obj.institution == '外包服务费':
            fee_rate = info_board.find_product_mandate_service_fee_rate(obj.product, date)
        elif obj.institution == '销售服务费':
            fee_rate = info_board.find_product_sell_service_fee_rate(obj.product, date)
        else:
            raise NotImplementedError(obj)
        value_obj = value_states.find_value(product=obj.product)
        obj.volume = round(obj.volume + fee_rate * value_obj.net_asset / 365, 2)
        # result_list.append(AccountPosition(
        #     product=obj.product, date=date, account_name=obj.account_name, institution=obj.institution,
        #     security_code=obj.security_code, currency=obj.currency, currency_origin=obj.currency_origin,
        #     volume=round(obj.volume + fee_rate * value_obj.net_asset / 365, 2),
        # ))

    # return result_list


def handle_management_fee_payable(
        info_board: jmInfoBoard,
        last_net_asset_list: List, last_management_fee_payable_list: List,
        product_range: set, date: datetime.date,
        logger: LogWrapper,
):
    """
    处理当日管理费计算和计提
        * 当日管理费
    :return:
    """
    acc_list = List()

    if date.year % 4 == 0:
        DAYS_ONE_YEAR = 366
    else:
        DAYS_ONE_YEAR = 365

    for product in product_range:

        fee_rate = info_board.find_product_management_fee_rate(product, date)
        logger.debug('寻找到产品 {} 管理费率为 {}'.format(product, fee_rate))
        # 费率为正
        if abs(fee_rate) > 0.0:
            last_net_asset = last_net_asset_list.find_value(product=product)
            assert isinstance(last_net_asset, AccountPosition)
            assert last_net_asset.account_name == '资产净值', '{}'.format(last_net_asset)

            try:
                last_fee_obj = last_management_fee_payable_list.find_value(product=product, account_name='累计应付管理费', )
            except ValueError:
                last_fee_obj = AccountPosition(
                    product=product, date=date, account_name='累计应付管理费', institution='-',
                    security_code='-', volume=0.0, market_value=0.0,
                    currency=last_net_asset.currency, currency_origin=last_net_asset.currency_origin,
                )
            assert isinstance(last_fee_obj, AccountPosition)

            fee_obj = AccountPosition().update(last_fee_obj)
            fee_obj.date = date
            assert fee_obj.account_name == '累计应付管理费'
            # fee_obj.volume = fee_obj.volume + last_net_asset.volume * fee_rate / 365
            fee_obj.volume = round(fee_obj.volume + last_net_asset.volume * fee_rate / DAYS_ONE_YEAR, 2)
            acc_list.append(fee_obj)

            # try:
            #     last_fee_obj = last_management_fee_payable_list.find_value(product=product, account_name='已付应付管理费',)
            # except ValueError:
            #     last_fee_obj = AccountPosition(
            #         product=product, date=date, account_name='已付应付管理费', institution='-',
            #         security_code='-', volume=0.0, market_value=0.0,
            #         currency=last_net_asset.currency, currency_origin=last_net_asset.currency_origin,
            #     )
            # assert isinstance(last_fee_obj, AccountPosition)
            #
            # fee_obj = AccountPosition().update(last_fee_obj)
            # fee_obj.date = date
            # assert fee_obj.account_name == '已付应付管理费'
            # acc_list.append(fee_obj)

        # 费率为零，可能是从收费转不收费
        else:
            try:
                last_fee_obj = last_management_fee_payable_list.find_value(
                    product=product, account_name='累计应付管理费', )
                assert isinstance(last_fee_obj, AccountPosition)
                fee_obj = AccountPosition().update(last_fee_obj)
                fee_obj.date = date
                assert fee_obj.account_name == '累计应付管理费'
                acc_list.append(fee_obj)
            except ValueError:
                pass

    return acc_list


def handle_management_fee_return(last_acc_pos: List, acc_pos: List, date: datetime.date):
    # TAG2
    """
    处理应收管理费返还
        * 管理费返还
    :return:
    """
    from modules.Modules import Modules

    if date.year % 4 == 0:
        DAYS_ONE_YEAR = 366
    else:
        DAYS_ONE_YEAR = 365

    env = Modules.get_instance()
    acc_list = List()

    for last_pos in last_acc_pos:
        assert isinstance(last_pos, AccountPosition)
        assert last_pos.institution == '久铭', '{}'.format(last_pos)

        fee_rate = env.info_board.find_product_management_return_rate(last_pos.product, last_pos.security_name, date)
        if abs(fee_rate) < 0.000001:
            continue

        try:
            fee_return = acc_pos.find_value(
                product=last_pos.product, account_name='累计应收管理费返还', security_name=last_pos.security_name)
        except ValueError:
            raise NotImplementedError(last_pos)
        assert isinstance(fee_return, AccountPosition)

        fee_return.volume = round(fee_return.volume + last_pos.market_value * fee_rate / DAYS_ONE_YEAR, 2)

    return acc_list


def handle_non_mandated_interest_receivable(entry_acc_list: List, date: datetime.date):
    from jetend.jmSheets import EntryAccount
    result_list = List()
    for obj in entry_acc_list:
        if obj.product == '稳健22号':
            continue
        assert isinstance(obj, EntryAccount)
        if abs(obj.net_value) >= 0.01:
            rece_obj = AccountPosition(
                product=obj.product, date=date, account_name='应收利息', institution=obj.base_account,
                security_code='-', volume=abs(obj.net_value),
                currency_origin='RMB', currency='RMB',
            )
            result_list.append(rece_obj)
    return result_list


def handle_account_interest_receivable(
        info_board: jmInfoBoard, acc_pos: List, last_acc_pos: List, date: datetime.date, product_range: tuple,
):
    """
    计提托管产品 银行账户、券商存出保证金产生的应收利息
    :return:
    """
    result_list = List()

    for product, sub_acc_pos in acc_pos.group_by_attr('product').items():
        if info_board.check_mandatory(product) is False:
            continue
        if product not in product_range:
            continue
        for acc in sub_acc_pos:
            if acc.institution in ('港股收益互换', '美股收益互换',):
                continue
            if abs(acc.volume) < 0.01:
                try:
                    last_rece_obj = last_acc_pos.find_value(
                        product=acc.product, institution=acc.institution, )
                except ValueError:
                    last_rece_obj = AccountPosition(
                        product=acc.product, date=date - datetime.timedelta(days=1), account_name='应收利息',
                        institution=acc.institution, security_code='-', security_name='', volume=0.0,
                        currency_origin=acc.currency_origin, currency=acc.currency,
                    )
                assert isinstance(last_rece_obj, AccountPosition)
                assert last_rece_obj.account_name == '应收利息', '{}'.format(last_rece_obj)

                rece_obj = AccountPosition().update(last_rece_obj)
                rece_obj.date = date
                result_list.append(rece_obj)
            else:
                interest_rate = info_board.find_product_account_interest_rate(
                    product=acc.product, account_type=acc.account_name, institution=acc.institution, date=date
                )
                try:
                    last_rece_obj = last_acc_pos.find_value(
                        product=acc.product, institution=acc.institution, )
                except ValueError:
                    last_rece_obj = AccountPosition(
                        product=acc.product, date=date - datetime.timedelta(days=1), account_name='应收利息',
                        institution=acc.institution, security_code='-', security_name='', volume=0.0,
                        currency_origin=acc.currency_origin, currency=acc.currency,
                    )
                assert isinstance(last_rece_obj, AccountPosition)
                assert last_rece_obj.account_name == '应收利息', '{}'.format(last_rece_obj)

                if interest_rate.interest_rate > 0.0:

                    rece_obj = AccountPosition().update(last_rece_obj)
                    rece_obj.date = date

                    if interest_rate.notes == '季度直接付息':
                        if date.month in (4, 7, 10, 1) and date.day == 1:
                            raise NotImplementedError('\n{}\n{}'.format(interest_rate, acc))
                        else:
                            pass
                    elif not is_valid_str(interest_rate.notes):
                        rece_obj.volume += round(
                            acc.volume * interest_rate.interest_rate / interest_rate.yearly_accrued_days, 2)
                    else:
                        raise NotImplementedError(interest_rate)

                    result_list.append(rece_obj)
                else:
                    rece_obj = AccountPosition().update(last_rece_obj)
                    rece_obj.date = date

                    if abs(rece_obj.volume) >= 0.01:
                        result_list.append(rece_obj)
                    else:
                        pass

    return result_list


def handle_dividend_receivable(
        last_acc_pos_list: List, acc_pos_list: List, dividend_info_list: List, date: datetime.date
):
    from jetend.jmSheets import DividendInfo
    result_list = List()

    currency_map = {'人民币': 'RMB', }

    for divi_info in dividend_info_list:
        assert isinstance(divi_info, DividendInfo)
        # 除权日 计提应收股利
        if divi_info.ex_date == date:
            pos_list = acc_pos_list.find_value_where(security_code=divi_info.security_code)
            assert divi_info.dividend_mode == '现金派息', '{}'.format(divi_info)
            for pos in pos_list:
                assert isinstance(pos, AccountPosition)
                divi_volume = divi_info.cash_dividend * pos.volume / divi_info.dividend_unit
                if divi_info.exchange_code in ('O',):
                    divi_volume = divi_volume * 0.7
                elif divi_info.exchange_code in ('SH', 'SZ'):
                    divi_volume = divi_volume
                elif divi_info.exchange_code in ('HK',):
                    divi_volume = divi_volume * 0.8
                else:
                    raise NotImplementedError('{}\n{}'.format(divi_info, pos))
                result_list.append(AccountPosition(
                    product=pos.product, date=date, account_name='应收股利', institution=pos.institution,
                    security_code=pos.security_code, security_name=pos.security_name,
                    volume=divi_volume, currency_origin=currency_map[divi_info.currency], currency=pos.currency,
                ))
        # 派息日 消除应收股利
        if divi_info.dividend_date == date:
            pos_list = acc_pos_list.find_value_where(account_name='应收股利', security_code=divi_info.security_code, )
            pos_list.extend(result_list.find_value_where(
                account_name='应收股利', security_code=divi_info.security_code, ))
            assert divi_info.dividend_mode == '现金派息', '{}'.format(divi_info)
            # TODO: 检查该券商是否有红利流水
            for pos in pos_list:
                assert isinstance(pos, AccountPosition)
                pos.volume = 0.0
        # if divi_info.ex_date < date < divi_info.dividend_date:
        #     last_divi_list = last_acc_pos_list.find_value_where(
        #         account_name='应收股利', security_code=divi_info.security_code
        #     )
        #     for last_divi in last_divi_list:
        #         divi_obj = AccountPosition().update(last_divi)
        #         divi_obj.date = date
        #         result_list.append(divi_obj)

    return result_list
