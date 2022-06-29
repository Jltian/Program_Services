# -*- encoding: UTF-8 -*-
import datetime

from extended.wrapper.MySQL import MySQL
from extended.wrapper.List import List
from extended import get_logger

from jetend.Constants import *
from jetend.DataCheck import *
from jetend.modules.jmInfoBoard import jmInfoBoard
from jetend.jmSheets import JiuMingTA


db = MySQL(server='192.168.1.31', port=3306, username='root', passwd='jm3389', )
db.log = get_logger('runTA')


def update_investor_info(db: MySQL):
    db.log.info('检查更新客户信息是否进入INVESTOR_BASIC')
    info_for_insert = list()
    compare_set = List(
        db.read_dict_query(DataBaseName.transfer_agent, """SELECT * FROM INVESTOR_BASIC;""")
    ).collect_key_value_set('code')
    # 获取久铭客户信息
    for obj_dict in db.read_dict_query(DataBaseName.transfer_agent_new, """SELECT * FROM 客户信息表;"""):
        if obj_dict['证件号'] not in compare_set:
            info_for_insert.append((obj_dict['证件号'], obj_dict['姓名']))
            compare_set.add(obj_dict['证件号'])
    # 获取静久客户信息
    for obj_dict in db.read_dict_query(DataBaseName.jingjiu_ta, """SELECT * FROM 客户信息表;"""):
        if obj_dict['证件类型'] not in compare_set:
            info_for_insert.append((obj_dict['证件类型'], obj_dict['姓名']))
            compare_set.add(obj_dict['证件类型'])
    for investor_code, investor_name in info_for_insert:
        db.execute(
            DataBaseName.transfer_agent,
            """INSERT INTO INVESTOR_BASIC(name, code) VALUES ('{}', '{}');""".format(investor_name, investor_code)
        )


def update_management_fee_provision(db: MySQL, current_date: datetime.date):
    """计提管理费"""
    db.log.info('开始计算 {} 管理费分摊'.format(current_date))
    # 确认管理费计提产品代码范围
    info_board = jmInfoBoard(db)
    product_code_range = List(db.read_dict_query(
        DataBaseName.transfer_agent, """
        SELECT * FROM PRODUCT_BASIC 
        WHERE belonging = '久铭' 
            AND (liquidation_date >= '{}' OR liquidation_date is NULL) 
            AND establishment_date <= '{}'
        ;""".format(current_date, current_date)
    )).collect_key_value_set('code')
    # product_code_range = List(db.read_dict_query(
    #     DataBaseName.transfer_agent,
    #     """SELECT * FROM PRODUCT_BASIC WHERE ;"""
    # )).collect_key_value_set('code')
    # 确认产品投资人与持仓
    current_holding_list = List()
    for product_code in product_code_range:
        current_holding_list.extend(List.from_dict_list(JiuMingTA.InvestorHolding, db.read_dict_query(
            DataBaseName.transfer_agent, """
            SELECT * FROM INVESTOR_HOLDING_RECORDS WHERE product_code = '{}' AND date = (
                SELECT MAX(date) FROM INVESTOR_HOLDING_RECORDS WHERE product_code = '{}' AND date <= '{}'
                );""".format(product_code, product_code, current_date - datetime.timedelta(days=1))
        )))
    # 确认管理费计提顺序
    product_management_fee_dict = dict()
    for product_code in product_code_range:
        db.log.debug('搜索管理费率 {}'.format(product_code))
        try:
            product_management_fee_dict[product_code] = db.read_dict_query(
                DataBaseName.transfer_agent, """
                SELECT `fee_rate` as fee_rate FROM PRODUCT_FEE_RATE 
                WHERE `product_code` = '{}' AND fee_type = '管理费率' AND date = (
                    SELECT max(date) FROM PRODUCT_FEE_RATE 
                    WHERE `date` <= '{}' AND `fee_type` = '管理费率' AND `product_code` = '{}'
                    );""".format(product_code, current_date, product_code)
            )[0]['fee_rate']
            assert is_valid_float(product_management_fee_dict[product_code]), '{} - {}'.format(
                product_code, product_management_fee_dict
            )
        except IndexError:
            assert int(current_holding_list.find_value_where(product_code=product_code).sum_attr('hold_volume')) == 0

    product_code_list_one, product_code_list_two = list(), list()
    for product_code, fee_rate in product_management_fee_dict.items():
        assert fee_rate >= 0, '当日管理费率为负 {}'.format(fee_rate)
        if fee_rate >= 0.00001:
            product_code_list_one.append(product_code)
        else:
            product_code_list_two.append(product_code)
    for i in range(len(product_code_list_two)):
        for j in range(i + 1, len(product_code_list_two), 1):
            code_i = product_code_list_two[i]
            code_j = product_code_list_two[j]
            if code_i in current_holding_list.find_value_where(product_code=code_j).collect_attr_set('investor_code'):
                product_code_list_two[i] = code_j
                product_code_list_two[j] = code_i
    if current_date.year % 4 == 0:
        DAYS_A_YEAR = 366
    else:
        DAYS_A_YEAR = 365
    product_fee_provision_list = List()
    # 对于本产品层面收管理费的产品，直接计提当日管理费
    for product_code in product_code_list_one:
        db.log.debug('计算固定管理费 {} {} {}'.format(
            product_code, info_board.find_product_info_by_code(product_code).name, current_date))
        fee_rate = product_management_fee_dict[product_code]
        # try:
        investor_holding_list = current_holding_list.find_value_where(product_code=product_code)
        if investor_holding_list.sum_attr('hold_volume') > 1.0:
            net_value = info_board.find_net_value_by_code(product_code, current_date - datetime.timedelta(days=1))
        else:
            continue
        # except AssertionError:
        #     net_value = 1.0
        for investor_code, investor_list in investor_holding_list.group_by_attr('investor_code').items():
            product_fee_provision_list.append(JiuMingTA.InvestorFeeProvision(
                date=current_date, investor_code=investor_code,
                product_code=product_code, fee_type='管理费',
                fee_amount=round(fee_rate * investor_list.sum_attr('hold_volume') * net_value / DAYS_A_YEAR, 4)
            ))
    # 对于在底层产品层面收管理费的产品，从底层产品管理费计提当日管理费
    for product_code in product_code_list_two:
        db.log.debug('计算固定管理费 {} {} {}'.format(
            product_code, info_board.find_product_info_by_code(product_code).name, current_date))
        total_fee = product_fee_provision_list.find_value_where(investor_code=product_code).sum_attr('fee_amount')
        investor_holding_list = current_holding_list.find_value_where(product_code=product_code)
        try:
            total_shares = investor_holding_list.find_value(investor_code='TOTAL_SHARES').hold_volume
        except ValueError:
            try:
                total_shares = investor_holding_list.find_value(investor_code=product_code).hold_volume
            except ValueError:
                if len(investor_holding_list) == 0:
                    continue
                else:
                    total_shares = investor_holding_list.sum_attr('hold_volume')
        for investor_code, investor_list in investor_holding_list.group_by_attr('investor_code').items():
            product_fee_provision_list.append(JiuMingTA.InvestorFeeProvision(
                date=current_date, investor_code=investor_code,
                product_code=product_code, fee_type='管理费',
                fee_amount=round(total_fee * investor_list.sum_attr('hold_volume') / total_shares, 4)
            ))
    db.execute(
        DataBaseName.transfer_agent, """
        DELETE FROM INVESTOR_FEE_PROVISION_RECORDS WHERE date = '{}' AND fee_type = '管理费'
        ;""".format(current_date)
    )
    db.insert_data_list(DataBaseName.transfer_agent, 'INVESTOR_FEE_PROVISION_RECORDS', product_fee_provision_list)


def update_management_fee_provision_details(db: MySQL, current_date: datetime.date):
    """计提管理费"""
    db.log.info('开始计算 {} 管理费分摊'.format(current_date))
    # 确认管理费计提产品代码范围
    info_board = jmInfoBoard(db)
    product_code_range = List(db.read_dict_query(
        DataBaseName.transfer_agent, """
        SELECT * FROM PRODUCT_BASIC 
        WHERE (liquidation_date >= '{}' OR liquidation_date is NULL) 
            AND establishment_date <= '{}'
        ;""".format(current_date, current_date)
    )).collect_key_value_set('code')
    # product_code_range = List(db.read_dict_query(
    #     DataBaseName.transfer_agent,
    #     """SELECT * FROM PRODUCT_BASIC WHERE ;"""
    # )).collect_key_value_set('code')
    # 确认产品投资人与持仓
    current_holding_list = List()
    for product_code in product_code_range:
        current_holding_list.extend(List.from_dict_list(JiuMingTA.InvestorHolding, db.read_dict_query(
            DataBaseName.transfer_agent, """
            SELECT * FROM INVESTOR_HOLDING_RECORDS WHERE product_code = '{}' AND date = (
                SELECT MAX(date) FROM INVESTOR_HOLDING_RECORDS WHERE product_code = '{}' AND date <= '{}'
                );""".format(product_code, product_code, current_date - datetime.timedelta(days=1))
        )))
    # 确认管理费计提顺序
    product_management_fee_dict = dict()
    for product_code in product_code_range:
        db.log.debug('搜索管理费率 {}'.format(product_code))
        try:
            product_management_fee_dict[product_code] = db.read_dict_query(
                DataBaseName.transfer_agent, """
                SELECT `fee_rate` as fee_rate FROM PRODUCT_FEE_RATE 
                WHERE `product_code` = '{}' AND fee_type = '管理费率' AND date = (
                    SELECT max(date) FROM PRODUCT_FEE_RATE 
                    WHERE `date` <= '{}' AND `fee_type` = '管理费率' AND `product_code` = '{}'
                    );""".format(product_code, current_date, product_code)
            )[0]['fee_rate']
            assert is_valid_float(product_management_fee_dict[product_code]), '{} - {}'.format(
                product_code, product_management_fee_dict
            )
        except IndexError:
            assert int(current_holding_list.find_value_where(product_code=product_code).sum_attr('hold_volume')) == 0

    # 先计提执行非0费率的计算，再执行穿透
    product_code_list_one, product_code_list_two = list(), list()
    for product_code, fee_rate in product_management_fee_dict.items():
        assert fee_rate >= 0, '当日管理费率为负 {}'.format(fee_rate)
        if fee_rate >= 0.00001:
            product_code_list_one.append(product_code)
        else:
            product_code_list_two.append(product_code)
    for i in range(len(product_code_list_two)):
        for j in range(i + 1, len(product_code_list_two), 1):
            code_i = product_code_list_two[i]
            code_j = product_code_list_two[j]
            if code_i in current_holding_list.find_value_where(product_code=code_j).collect_attr_set('investor_code'):
                product_code_list_two[i] = code_j
                product_code_list_two[j] = code_i
    if current_date.year % 4 == 0:
        DAYS_A_YEAR = 366
    else:
        DAYS_A_YEAR = 365
    product_fee_provision_list = List()
    # 对于本产品层面收管理费的产品，直接计提当日管理费
    for product_code in product_code_list_one:
        db.log.debug('计算固定管理费 {} {} {}'.format(
            product_code, info_board.find_product_info_by_code(product_code).name, current_date))
        fee_rate = product_management_fee_dict[product_code]
        # try:
        investor_holding_list = current_holding_list.find_value_where(product_code=product_code)
        if investor_holding_list.sum_attr('hold_volume') > 1.0:
            net_value = info_board.find_net_value_by_code(product_code, current_date - datetime.timedelta(days=1))
        else:
            continue
        for inv_hold_item in investor_holding_list:
            product_fee_provision_list.append(JiuMingTA.InvestorFeeProvision(
                date=current_date, investor_code=inv_hold_item.investor_code,
                product_code=product_code, fee_type='管理费',
                fee_amount=round(fee_rate * inv_hold_item.hold_volume * net_value / DAYS_A_YEAR, 4),
                purchase_id=inv_hold_item.purchase_id,
            ))
    # 对于在底层产品层面收管理费的产品，从底层产品管理费计提当日管理费
    for product_code in product_code_list_two:
        db.log.debug('计算固定管理费 {} {} {}'.format(
            product_code, info_board.find_product_info_by_code(product_code).name, current_date))
        total_fee = product_fee_provision_list.find_value_where(
            investor_code=product_code
        ).sum_attr('fee_amount')
        investor_holding_list = current_holding_list.find_value_where(product_code=product_code)
        try:
            total_shares = investor_holding_list.find_value(investor_code='TOTAL_SHARES').hold_volume
        except ValueError:
            try:
                total_shares = investor_holding_list.find_value(investor_code=product_code).hold_volume
            except ValueError:
                if len(investor_holding_list) == 0:
                    continue
                else:
                    total_shares = investor_holding_list.sum_attr('hold_volume')
        for inv_hold_item in investor_holding_list:
            if product_code == 'SJQ420':
                continue
            else:
                product_fee_provision_list.append(JiuMingTA.InvestorFeeProvision(
                    date=current_date, investor_code=inv_hold_item.investor_code,
                    product_code=product_code, fee_type='管理费',
                    fee_amount=round(total_fee * inv_hold_item.hold_volume / total_shares, 4),
                    purchase_id=inv_hold_item.purchase_id,
                ))
    db.execute(
        DataBaseName.transfer_agent, """
        DELETE FROM INVESTOR_FEE_PROVISION_RECORDS WHERE date = '{}' AND fee_type = '管理费'
        ;""".format(current_date)
    )
    db.insert_data_list(DataBaseName.transfer_agent, 'INVESTOR_FEE_PROVISION_RECORDS', product_fee_provision_list)


def update_investor_holding(db: MySQL, product_code: str, identifier: str = 'JM'):
    assert identifier in ('JM', 'JJKM'), 'identifier should be '
    info_board = jmInfoBoard(db)
    product_full_name = info_board.find_product_info_by_code(product_code).full_name
    db.log.debug('检查客户持仓是否根据申赎流水更新到最新：{} {}'.format(product_code, product_full_name))
    # begin_date = db.read_dict_query(        # 最早日期
    #     'test', """SELECT MIN(confirmation_date) as confirmation_date FROM 申赎流水表;"""
    # )[0]['confirmation_date']
    begin_date = db.read_dict_query(      # 最后更新日期
        DataBaseName.transfer_agent,
        """SELECT MAX(date) as date FROM INVESTOR_HOLDING_RECORDS WHERE product_code = '{}';""".format(product_code)
    )[0]['date']
    if identifier == 'JM':
        current_ta_list = List.from_dict_list(JiuMingTA.TransferAgentFlow, db.read_dict_query(
            DataBaseName.transfer_agent_new, """
            SELECT * FROM 申赎流水表 WHERE product_name = '{}' ORDER BY confirmation_date
            ;""".format(product_full_name)
        ))                                    # 该产品申赎流水
        end_date = db.read_dict_query(
            DataBaseName.transfer_agent_new, """
            SELECT MAX(confirmation_date) as confirmation_date FROM 申赎流水表 WHERE product_name = '{}'
            ;""".format(product_full_name)
        )[0]['confirmation_date']
    else:
        current_ta_list = List.from_dict_list(JiuMingTA.TransferAgentFlow, db.read_dict_query(
            DataBaseName.jingjiu_ta, """
            SELECT * FROM 申赎流水表 WHERE product_name = '{}' ORDER BY confirmation_date
            ;""".format(product_full_name)
        ))
        # db.log.debug(current_ta_list)
        end_date = db.read_dict_query(
            DataBaseName.jingjiu_ta, """
            SELECT MAX(confirmation_date) as confirmation_date FROM 申赎流水表 WHERE product_name = '{}'
            ;""".format(product_full_name)
        )[0]['confirmation_date']

    # end_date = max(end_date, datetime.date.today())
    if begin_date is None:
        begin_date = min(current_ta_list.collect_attr_set('confirmation_date')) - datetime.timedelta(days=2)
    else:
        current_total = List.from_dict_list(JiuMingTA.InvestorHolding, db.read_dict_query(
            DataBaseName.transfer_agent,
            """SELECT * FROM INVESTOR_HOLDING_RECORDS WHERE product_code = '{}' AND date = '{}'
            ;""".format(product_code, begin_date)
        ))
        try:
            while max(current_ta_list.collect_attr_set('confirmation_date')) > begin_date:
                current_ta_list.pop(-1)
        except ValueError as error_value:
            db.log.error(current_ta_list)
            raise error_value
        while round(current_total.find_value_where(investor_code='TOTAL_SHARES').sum_attr('hold_volume'), 2) != round(
            current_ta_list.sum_attr('share'), 2
        ):
            db.log.debug(
                '更正前值错误：{}, {}, {}'.format(product_full_name, begin_date, (
                    current_total.find_value_where(investor_code='TOTAL_SHARES').sum_attr('hold_volume')
                    - current_ta_list.sum_attr('share'))))
            # print(
            #     '更正前值错误：', product_full_name, begin_date, (
            #         current_total.find_value_where(investor_code='TOTAL_SHARES').sum_attr('hold_volume')
            #         - current_ta_list.sum_attr('share'))
            # )
            current_ta_list.pop()

            try:
                begin_date = max(current_ta_list.collect_attr_set('confirmation_date'))
            except:
                print(product_code)
                raise Exception
            current_total = List.from_dict_list(JiuMingTA.InvestorHolding, db.read_dict_query(
                DataBaseName.transfer_agent,
                """SELECT * FROM INVESTOR_HOLDING_RECORDS WHERE product_code = '{}' AND date = '{}'
                ;""".format(product_code, begin_date)
            ))
            db.log.debug('准确持仓信息起始点迁移至 {}'.format(max(current_ta_list.collect_attr_set('date'))))
        # if len(current_total) == 0:     # 新产品，倒退回认购时间点
        #     begin_date = min(current_ta_list.collect_attr_set('confirmation_date')) - datetime.timedelta(days=2)
        if begin_date >= end_date and round(
                current_total.find_value(investor_code='TOTAL_SHARES').hold_volume, 2
        ) == round(current_ta_list.sum_attr('share'), 2):
            db.execute(
                DataBaseName.transfer_agent, """
                DELETE FROM INVESTOR_HOLDING_RECORDS WHERE date > '{}' AND product_code = '{}'
                ;""".format(end_date, product_code))
            return

    iter_date = begin_date + datetime.timedelta(days=1)

    while iter_date <= end_date:
        db.log.info('searching {}-{} date {}'.format(product_code, product_full_name, iter_date))
        holding_list = List()
        for obj in List.from_dict_list(JiuMingTA.InvestorHolding, db.read_dict_query(
                DataBaseName.transfer_agent,
                """SELECT * FROM INVESTOR_HOLDING_RECORDS WHERE date = '{}' AND product_code = '{}'
                ;""".format(iter_date - datetime.timedelta(days=1), product_code)
        )):
            # 负数份额
            if obj.hold_volume < 0:
                raise RuntimeError(obj)
            elif obj.hold_volume == 0:
                continue
            elif obj.investor_code == 'TOTAL_SHARES':
                continue
            else:
                obj.date = iter_date
                holding_list.append(obj)
        if identifier == 'JM':
            current_ta_list = List.from_dict_list(JiuMingTA.TransferAgentFlow, db.read_dict_query(
                DataBaseName.transfer_agent_new,
                """SELECT * FROM 申赎流水表 WHERE confirmation_date = '{}' AND product_name = '{}'
                ;""".format(iter_date, product_full_name)
            ))
        else:
            current_ta_list = List.from_dict_list(JiuMingTA.TransferAgentFlow, db.read_dict_query(
                DataBaseName.jingjiu_ta,
                """SELECT * FROM 申赎流水表 WHERE confirmation_date = '{}' AND product_name = '{}'
                ;""".format(iter_date, product_full_name)
            ))
        post_current_in, post_current_out = List(), List()
        for ta_obj in current_ta_list:
            db.log.debug(ta_obj)
            # 先进先出？？？
            if abs(ta_obj.fee) < 0.01:
                pass
            else:
                pass
                # assert round(ta_obj.amount, 2) == round(ta_obj.netvalue * ta_obj.share, 2), ta_obj
            if ta_obj.type == '认购':
                person_list = holding_list.find_value_where(
                    investor_code=ta_obj.idnumber, product_code=product_code
                )
                if len(person_list) == 0:
                    holding_list.append(JiuMingTA.InvestorHolding(
                        date=iter_date, investor_code=ta_obj.idnumber, investor_name=ta_obj.name,
                        product_code=product_code, performace_date=ta_obj.date,
                        performace_cost=ta_obj.netvalue, hold_volume=ta_obj.share,
                        purchase_id=ta_obj.purchase_id,
                    ))
                elif len(person_list) == 1:
                    obj = person_list[0]
                    # assert obj.purchase_id == ta_obj.purchase_id, '\n{}\n{}'.format(obj, ta_obj)
                    assert round(obj.performace_cost, 3) == round(ta_obj.netvalue, 3), '{}\n{}'.format(obj, ta_obj)
                    obj.hold_volume += abs(ta_obj.share)
                    obj.hold_volume = round(obj.hold_volume, 2)
                else:
                    raise RuntimeError('{}\n{}'.format(ta_obj, person_list))
            elif ta_obj.type in ('申购', '基金转入'):
                person_list = holding_list.find_value_where(
                    investor_code=ta_obj.idnumber, product_code=product_code,
                    purchase_id=ta_obj.purchase_id,
                )
                if len(person_list) == 1:
                    obj = person_list[0]
                    obj.hold_volume += abs(ta_obj.share)
                elif len(person_list) == 0:
                    holding_list.append(JiuMingTA.InvestorHolding(
                        date=iter_date, investor_code=ta_obj.idnumber, investor_name=ta_obj.name,
                        product_code=product_code, performace_date=ta_obj.date,
                        performace_cost=ta_obj.netvalue, hold_volume=ta_obj.share,
                        purchase_id=ta_obj.purchase_id,
                    ))
                else:
                    raise RuntimeError(ta_obj)
            elif ta_obj.type == '份额转出':
                # 份额转出
                person_list = holding_list.find_value_where(
                    investor_code=ta_obj.idnumber, product_code=product_code,
                    purchase_id=ta_obj.purchase_id,
                )
                if len(person_list) == 1:
                    obj = person_list[0]
                    if obj.hold_volume == ta_obj.share:
                        obj.investor_code = '转出份额|待转入'
                    else:
                        holding_list.append(JiuMingTA.InvestorHolding(
                            date=iter_date, investor_code='转出份额|待转入',
                            product_code=product_code, performace_date=obj.performace_date,
                            performace_cost=obj.performace_cost, hold_volume=abs(ta_obj.share),
                            purchase_id=ta_obj.purchase_id,
                        ))
                        obj.hold_volume = round(obj.hold_volume - abs(ta_obj.share), 2)
                elif len(person_list) > 1:
                    raise NotImplementedError(ta_obj)
                else:
                    raise RuntimeError(ta_obj)
            elif ta_obj.type == '计提业绩报酬':
                if ta_obj.share > 0:
                    post_current_in.append(ta_obj)
                else:
                    # 直接扣除份额，业绩日期移至计提日
                    person_list = holding_list.find_value_where(
                        investor_code=ta_obj.idnumber, product_code=product_code,
                        purchase_id=ta_obj.purchase_id,
                    )
                    if len(person_list) == 1:
                        obj = person_list[0]
                        obj.hold_volume = round(obj.hold_volume - abs(ta_obj.share), 2)
                        assert obj.hold_volume >= 0, obj
                        obj.performace_date = ta_obj.date
                        obj.performace_cost = ta_obj.netvalue
                    elif len(person_list) > 1:
                        raise NotImplementedError(ta_obj)
                    else:
                        raise RuntimeError('{}\n{}'.format(ta_obj, person_list))
            elif ta_obj.type in ('份额转入', ):
                post_current_in.append(ta_obj)
            elif ta_obj.type in ('赎回', '赎回业绩报酬', '基金转出业绩报酬', '基金转出'):
                post_current_out.append(ta_obj)
            elif ta_obj.type in ('分红', ):
                pass
            else:
                raise NotImplementedError(ta_obj)
        post_current_in.extend(post_current_out)
        for ta_obj in post_current_in:
            if ta_obj.type == '份额转入':
                person_list = holding_list.find_value_where(
                    investor_code='转出份额|待转入', product_code=product_code,
                )
                if len(person_list) == 1:
                    # 转入转出政策：视为新买入
                    obj = person_list[0]
                    obj.investor_code = ta_obj.idnumber
                    obj.investor_name = ta_obj.name
                    obj.performace_cost = ta_obj.netvalue
                    obj.purchase_id = ta_obj.purchase_id
                    obj.performace_date = ta_obj.date
                    assert obj.hold_volume == ta_obj.share, '{}\n{}'.format(obj, ta_obj)
                    # raise NotImplementedError('{}\n{}'.format(ta_obj, person_list))
                else:
                    other_list = post_current_in.find_value_where(
                            product_code=product_code, type='份额转入', idnumber=ta_obj.idnumber
                    )
                    if person_list.sum_attr('hold_volume') == other_list.sum_attr('share'):
                        # 转入转出政策：视为新买入
                        holding_list.append(JiuMingTA.InvestorHolding(
                            date=iter_date, investor_code=ta_obj.idnumber,
                            product_code=product_code, performace_date=ta_obj.date,
                            performace_cost=ta_obj.netvalue, hold_volume=ta_obj.share,
                            purchase_id=ta_obj.purchase_id,
                        ))
                        for obj in person_list:
                            obj.hold_volume = 0
                    else:
                        volume_to_in = abs(ta_obj.share)
                        for obj in person_list:
                            if obj.hold_volume >= volume_to_in > 0:
                                obj.hold_volume = round(obj.hold_volume - volume_to_in, 2)
                                holding_list.append(JiuMingTA.InvestorHolding(
                                    date=iter_date, investor_code=ta_obj.idnumber, investor_name=ta_obj.name,
                                    product_code=product_code, performace_date=ta_obj.date,
                                    performace_cost=ta_obj.netvalue, hold_volume=ta_obj.share,
                                    purchase_id=ta_obj.purchase_id,
                                ))
                                break
                            elif obj.hold_volume == 0.0:
                                continue
                            else:
                                volume_to_in = round(volume_to_in - abs(obj.hold_volume), 2)
                                obj.hold_volume = 0.0
                        assert person_list.sum_attr('hold_volume') >= 0, '{}\n{}'.format(person_list, other_list)
                        print(person_list)
                        print(ta_obj)
                        # print(other_list)
                        # raise NotImplementedError(ta_obj)
            elif ta_obj.type == '计提业绩报酬':
                # 类同申购
                assert ta_obj.share > 0, ta_obj
                person_list = holding_list.find_value_where(
                    investor_code=ta_obj.idnumber, product_code=product_code,
                    purchase_id=ta_obj.purchase_id,
                )
                if len(person_list) == 1:
                    obj = person_list[0]
                    obj.hold_volume += abs(ta_obj.share)
                elif len(person_list) == 0:
                    holding_list.append(JiuMingTA.InvestorHolding(
                        date=iter_date, investor_code=ta_obj.idnumber, investor_name=ta_obj.name,
                        product_code=product_code, performace_date=ta_obj.date,
                        performace_cost=ta_obj.netvalue, hold_volume=ta_obj.share,
                        purchase_id=ta_obj.purchase_id,
                    ))
                else:
                    raise RuntimeError(ta_obj)
            elif ta_obj.type in ('赎回', '赎回业绩报酬', '基金转出业绩报酬', '基金转出'):
                if ta_obj.idnumber in (
                        '140202197708121032',       # 王华
                        '370211197402040044',       # 王萍
                        '91310115681003089D',       # 久铭投资
                ):
                    person_list = holding_list.find_value_where(
                        investor_code=ta_obj.idnumber, product_code=product_code,
                    )
                    sorted(person_list, key=lambda s: s.purchase_id, )
                    volume_to_out = ta_obj.share
                    for obj in person_list:
                        if obj.hold_volume >= abs(volume_to_out) > 0:
                            obj.hold_volume = round(obj.hold_volume - abs(volume_to_out), 2)
                            break
                        elif obj.hold_volume == 0.0:
                            continue
                        else:
                            volume_to_out = round(volume_to_out + abs(obj.hold_volume), 2)
                            obj.hold_volume = 0.0
                else:
                    # 赎回对应的份额
                    person_list = holding_list.find_value_where(
                        investor_code=ta_obj.idnumber, product_code=product_code,
                        purchase_id=ta_obj.purchase_id,
                    )
                    if len(person_list) == 1:
                        if product_full_name == '静康1号私募证券投资基金':
                            print("zaiting")
                        obj = person_list[0]
                        obj.hold_volume -= abs(ta_obj.share)
                        obj.hold_volume = round(obj.hold_volume, 2)
                        assert obj.hold_volume >= 0, obj
                    elif len(person_list) > 1:
                        raise NotImplementedError(ta_obj)
                    else:
                        raise RuntimeError('{}\n{}'.format(ta_obj, holding_list.find_value_where(
                                product_code=product_code,
                            )))
            else:
                raise NotImplementedError(ta_obj)
        product_code_set = holding_list.collect_attr_set('product_code')
        for product_code in product_code_set:
            person_list = holding_list.find_value_where(product_code=product_code)
            holding_list.append(JiuMingTA.InvestorHolding(
                date=iter_date, investor_code='TOTAL_SHARES',
                product_code=product_code, performace_date=iter_date,
                performace_cost=1.0, hold_volume=round(person_list.sum_attr('hold_volume'), 2),
                purchase_id='-',
            ))

            # assert holding_list[-1].hold_volume
            # raise RuntimeError(holding_list[-1])
        # 检查份额合法性
        for obj in holding_list:
            if obj.hold_volume < 0:
                raise RuntimeError(obj)
            elif 0 < obj.hold_volume < 100:
                assert holding_list.find_value_where(
                    investor_code=obj.investor_code
                ).sum_attr('hold_volume') > 1000, holding_list.find_value_where(
                    investor_code=obj.investor_code
                )
            else:
                pass
        db.execute(
            DataBaseName.transfer_agent, """
            DELETE FROM INVESTOR_HOLDING_RECORDS WHERE date = '{}' AND product_code = '{}'
            ;""".format(iter_date, product_code))
        db.insert_data_list(DataBaseName.transfer_agent, 'INVESTOR_HOLDING_RECORDS', holding_list)
        # raise RuntimeError(holding_list)
        iter_date += datetime.timedelta(days=1)


def update_net_value_from_hand_input_to_machine_recored(db: MySQL):
    """更新jiuming_ta_new.净值表 -> transfer_agent.PRODUCT_NET_VALUE"""
    product_info_list = db.read_dict_query(
        DataBaseName.transfer_agent,
        """SELECT code, name, belonging FROM PRODUCT_BASIC;"""
    )
    date_range_set = List(
        db.read_dict_query(DataBaseName.transfer_agent_new, """SELECT 日期 FROM 净值表;""")
    ).collect_attr_set('日期')
    for p_info_dict in product_info_list:
        p_code, p_name, p_belonging = p_info_dict['code'], p_info_dict['name'], p_info_dict['belonging']
        p_date_set = List(db.read_dict_query(
            DataBaseName.transfer_agent,
            """SELECT date FROM PRODUCT_NET_VALUE WHERE product_code = '{}';""".format(p_code)
        )).collect_attr_set('date')
        db.log.info('CHECK NET_VALUE_UPDATE {}'.format(p_info_dict))
        for date in date_range_set - p_date_set:
            if p_belonging == '久铭':
                net_value = db.read_dict_query(
                    DataBaseName.transfer_agent_new,
                    """SELECT {} FROM 净值表 WHERE 日期 = '{}';""".format(p_name, date)
                )
            else:
                net_value = db.read_dict_query(
                    DataBaseName.jingjiu_ta,
                    """SELECT {} FROM 静久净值表 WHERE 日期 = '{}';""".format(p_name, date)
                )
            if len(net_value) == 0:
                continue
            else:
                net_value = net_value[0][p_name]
            if is_valid_float(net_value):
                new_net_obj = {'product_code': p_code, 'product_name': p_name, 'date': date, 'net_value': net_value}
                db.insert_data_obj(DataBaseName.transfer_agent, 'PRODUCT_NET_VALUE', new_net_obj)
                db.log.debug('INSERT TO PRODUCT_NET_VALUE {}'.format(new_net_obj))
            else:
                continue


def update_and_release_product_net_value(db: MySQL):
    """更新transfer_agent.PRODUCT_NET_VALUE_RELEASED"""
    accumulated_map_dict = {
        # '专享16号': 0.0, '稳健1号': 0.0,
       '创新稳禄3号': 0.0,'专享29号':0.0,'专享26号':0.0,'专享25号':0.0
    }
    for product in (
        #'专享16号', '稳健1号',
        '创新稳禄3号','专享29号','专享26号','专享25号'
    ):
        product_net_value_list = db.read_dict_query(
            DataBaseName.transfer_agent,
            """SELECT * FROM PRODUCT_NET_VALUE WHERE product_name = '{}';""".format(product)
        )
        for nv_obj in product_net_value_list:
            if len(db.read_dict_query(
                DataBaseName.transfer_agent,
                """SELECT * FROM PRODUCT_NET_VALUE_RELEASED WHERE product_name = '{}' AND date = '{}';""".format(
                    product, nv_obj['date']
                )
            )) > 0 or (nv_obj['date'] < datetime.date(2020, 11, 6) and nv_obj['date'].isoweekday() != 5):
                continue
            else:
                nv_obj['accumulated_net_value'] = nv_obj['net_value'] + accumulated_map_dict[product]
                db.insert_data_obj(DataBaseName.transfer_agent, 'PRODUCT_NET_VALUE_RELEASED', nv_obj)
                db.log.debug('INSERT TO PRODUCT_NET_VALUE {}'.format(nv_obj))


def update_all_product_related(db: MySQL):
    update_investor_info(db)
    info_board = jmInfoBoard(db)
    # 更新久铭份额明细表
    for info_dict in db.read_dict_query(
            DataBaseName.transfer_agent_new,
            """SELECT DISTINCT product_name as product_name FROM 申赎流水表;"""
    ):
        product_name = info_dict['product_name']
        product_code = info_board.find_product_code_by_name(product_name)
        #'SL0795','SN0910','SCR398'
        if product_code in  ('SGV459','SLZ605','SQL786','SL0795'):
            continue
        else:
            update_investor_holding(db, product_code, identifier='JM')
    # #更新静康份额明细表
    for info_dict in db.read_dict_query(
            DataBaseName.jingjiu_ta,
            """SELECT DISTINCT product_name as product_name FROM 申赎流水表;"""
    ):
        product_name = info_dict['product_name']
        product_code = info_board.find_product_code_by_name(product_name)
        update_investor_holding(db, product_code, identifier='JJKM')

    #更新固定管理费
    # iter_date = datetime.date(2021, 6, 20)
    # while iter_date <= datetime.date(2021, 9, 30):
    #     update_management_fee_provision_details(db, iter_date)
    #     iter_date += datetime.timedelta(days=1)

    # 更新jiuming_ta_new.净值表 -> transfer_agent.PRODUCT_NET_VALUE
    update_net_value_from_hand_input_to_machine_recored(db)
    # 更新transfer_agent.PRODUCT_NET_VALUE_RELEASED
    update_and_release_product_net_value(db)


update_all_product_related(db)
#update_and_release_product_net_value(db)
