from utils.MysqlProxy import MysqlProxy


def insert_account(array):
    for item in range(len(array)):
        if array[item] == '' or array[item] == None:
            array[item] = 'Null'
        else:
            pass

    print(param_1, param_2)
    sql = """insert into jm_statement.account_information (`product`,`belong`,`type`,`account`,`card_sh`,`card_sz`,`start_date`,`business_department`,`contacts`,`contact_email`,`contact_mob`,`contact_tel`,`contact_weixin`,`status`,`trader`,`salesman`,`backstage_staff`,`notes`) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) """
    mp = MysqlProxy()
    id_number = mp.create(sql, array)
    return id_number
    # return JsonResponse({})
