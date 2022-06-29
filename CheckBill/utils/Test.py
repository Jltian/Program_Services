import datetime
from utils.ProductT2 import ProductT2
import Interfaces
# str = datetime.datetime.today().date().strftime("%Y-%m-%d")
# pt = ProductT2()
# pt.__int__()
# pt.primary()
# str1 = datetime.date.strftime(pt.t2day[0]['date'],"%Y-%m-%d")
# print(type(str1))
# print(str1)

id_num = Interfaces.insert_account('qq', ['神奇1号','神奇券商','神奇账户','神账户号','','','2022-02-10','上海陆佳嘴','张三','sanyou@fafa','1367664336','254646','hsaaigh','1','','','',''])
print(id_num)