# -*- encoding: UTF-8 -*-
import os
import datetime

from jetend.structures import MySQL

from trade.TradeLoader import TradeFlowLoader

base_folder, date_list = r'Z:\当日交易流水', list()
for file_tag in os.listdir(base_folder):
    assert file_tag.startswith('当日成交')
    if os.path.isdir(os.path.join(base_folder, file_tag)):
        date_list.append(datetime.datetime.strptime(
            file_tag[4:12], '%Y%m%d'
        ).date())
    else:
        if file_tag.lower().endswith('rar'):
            os.remove(os.path.join(base_folder, file_tag))
        else:
            pass
CURRENT_RUNNING_DATE = max(date_list)

# CURRENT_RUNNING_DATE = datetime.date(2020, 3, 6)

loader = TradeFlowLoader(
    MySQL('root', 'jm3389', '192.168.1.31', 3306),
    r'Z:\当日交易流水'
)
loader.load_simple_output_flow(CURRENT_RUNNING_DATE)
# loader.update_account_deposition(CURRENT_RUNNING_DATE)
loader.update_security_position(CURRENT_RUNNING_DATE)
loader.compare_security_position(CURRENT_RUNNING_DATE)

loader.log.info_running('前一日：{} 当前日：{} 后一日：{}'.format(
    loader.current_date - datetime.timedelta(days=1), loader.current_date,
    loader.current_date + datetime.timedelta(days=1)
))
# loader.save_to_database()
