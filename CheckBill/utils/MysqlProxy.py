import pymysql


class MysqlProxy(object):

    def __init__(self):
        self.conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd='jm3389', db='jm_statement')
        self.cursor = self.conn.cursor(cursor=pymysql.cursors.DictCursor)

    # 获取多个
    def get_list(self, sql, args):
        self.cursor.execute(sql, args)
        result_list = self.cursor.fetchall()
        return result_list

    # 获取单个
    def get_one(self, sql, args):
        self.cursor.execute(sql, args)
        result = self.cursor.fetchone()
        return result

    # 添加、删除不返回方法，【应该还有个修改功能】
    def modify(self, sql, args):
        self.cursor.execute(sql, args)
        self.conn.commit()

    # 支持批量存入一个列表元组
    def multiple_modify(self, sql, args):
        self.cursor.executemany(sql, args)
        self.conn.commit()

    # 添加、删除返回id操作
    def create(self, sql, args):
        self.cursor.execute(sql, args)
        self.conn.commit()
        return self.cursor.lastrowid

    # 关闭操作
    def close(self):
        self.cursor.close()
        self.conn.close()
