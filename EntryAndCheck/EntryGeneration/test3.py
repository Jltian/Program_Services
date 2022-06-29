import pymysql

date = '20211018'

#打开数据库连接
db = pymysql.connect(host='192.168.1.31', port=3306, user='root', passwd='jm3389', db='jm_statement', charset='utf8')
cursor = db.cursor()  # 使用cursor()方法获取操作游标

sql = "INSERT INTO `statement_arrive_copy` (`id`, `start_date`, `end_date`, `file_name`, `status`) " \
      "VALUES ('265', '%s', '%s', '01125828久铭稳健1号-20211018.txt', '1');" %(date,date)
cursor.execute(sql)
db.commit()
cursor.close()  # 关闭游标
db.close()  # 关闭数据库连接