# -*- encoding: UTF-8 -*-
from plan.utils.MysqlProxy import MysqlProxy

mp = MysqlProxy('jm_statement')
sql = 'select * from account_information where id = %s'
res = mp.get_one(sql,[1])
print(res)