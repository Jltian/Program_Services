import datetime
import time

from utils.MysqlProxy import MysqlProxy


# Create your tests here.
class ProductT2(object):
    def __int__(self):
        self.valid_count = 0
        self.t2day = ''
    def primary(self):
        stamp = datetime.datetime.today().date()
        #print(stamp.strftime("%Y-%m-%d"))
        #print(type(stamp.strftime("%Y-%m-%d")))
        #stamp = datetime.date(2021,10,26)
        self.pop_t2_day(stamp.strftime("%Y-%m-%d"))
        return self.t2day[0]['date']
    def pop_t2_day(self,currentday):
        currentday = self.sub_one_day(currentday)
        sql = "SELECT * FROM jm_statement.trade_date td where td.date = %s"
        result_list = MysqlProxy().get_list(sql,currentday)
        if len(result_list)>0:
            self.valid_count = self.valid_count + 1
            if self.valid_count == 2:
                self.t2day = result_list
            else:
                self.pop_t2_day(currentday)
        else:
            self.pop_t2_day(currentday)
    def sub_one_day(self,day):
        #datetime.datetime.strptime(day, "%Y-%m-%d").date()
        cur_day = datetime.datetime.strptime(day, '%Y-%m-%d')
        yesterday_stamp = cur_day.timestamp() - (60*60*24)
        #print(yesterday_stamp)
        date_yesterday = time.localtime(yesterday_stamp)
        return time.strftime('%Y-%m-%d',date_yesterday)

if __name__ == '__main__':
    pt = ProductT2()
    pt.__int__()
    pt.primary()
