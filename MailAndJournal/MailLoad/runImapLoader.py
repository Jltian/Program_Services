# -*- encoding: UTF-8 -*-
import datetime
import os
import pickle
import time

from core.ImapLoader import ImapLoader

FIRST_RUN = True
while True:
    current_time = datetime.datetime.now()
    # 夜间不运行
    #if current_time.hour in (0, 1, 2, 3, 4, 5, 20, 21, 22, 23, 24):
    if current_time.hour in (3, 4, 5):
        time.sleep(160)
        continue
    # 每小时只运行一次，若遇到第一次运行不受此限制
    if 0 <= current_time.minute <= 3 or FIRST_RUN is True:
        FIRST_RUN = False
    else:
        time.sleep(160)
        continue
    # SINCE_DATE = datetime.date(2020, 9, 28)
    SINCE_DATE = datetime.date.today() - datetime.timedelta(days=5)

    settings = {
        'mail_bit_path': r'D:\FundValuation\久铭估值专用邮箱缓存\邮件IMAP编码数据',
        'mail_content_path': r'D:\FundValuation\久铭估值专用邮箱缓存\邮件IMAP解码数据',
        'mail_classification_path': r'D:\FundValuation\估值可用磁盘数据\久铭邮件账户分类保存',
        'mail_db': r'D:\FundValuation\久铭估值专用邮箱缓存\jiuming_mails.db',
    }
    settings.update(pickle.load(
        open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'core', 'jiuming.pick'), 'rb'))
    )

    loader = ImapLoader(settings)
    loader.update_mail_data_base(
        since_date=SINCE_DATE,
        # on_date=datetime.date(2019, 10, 20),
    )
    loader.update_mail_content_cache()
    loader.update_mail_classification(
        folder_tag='久铭',
        range_start=SINCE_DATE,
        # range_end=datetime.date(2019, 9, 6),
    )



    settings = {
        'mail_bit_path': r'D:\FundValuation\静久估值专用邮箱缓存\邮件IMAP编码数据',
        'mail_content_path': r'D:\FundValuation\静久估值专用邮箱缓存\邮件IMAP解码数据',
        'mail_classification_path': r'D:\FundValuation\估值可用磁盘数据\久铭邮件账户分类保存',
        'mail_db': r'D:\FundValuation\静久估值专用邮箱缓存\jingjiu_mails.db',
    }
    # res = {'server_address': 'pop.exmail.qq.com',
    #        'user_account': 'gzzy@jingjiukm.com',
    #        'user_password': 'JINGj123'}
    settings.update(pickle.load(
        open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'core', 'jjkm.pick'), 'rb'))
    )

    loader = ImapLoader(settings)
    loader.update_mail_data_base(
        since_date=SINCE_DATE,
        # on_date=datetime.date(2019, 10, 20),
    )
    loader.update_mail_content_cache()
    loader.update_mail_classification(
        folder_tag='静久',
        range_start=SINCE_DATE,
        # range_end=datetime.date(2019, 9, 6),
    )

    loader.log.info_running('本次运行结束', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
