from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
import datetime
# Create your views here.
from account.models import Information
from utils.MysqlProxy import MysqlProxy
from utils.ProductT2 import ProductT2
from django.core.cache import cache


def get_bills(request):
    # ps_all = Information.objects.all()
    token = request.GET.get("token")
    login_user_list = cache.get("login_user")
    global login_user
    try:
        for lu in login_user_list:
            if lu[token] is not None:
                login_user = lu[token]
    except TypeError:
        return JsonResponse({"status_code": '302', "message": "登录已失效或被刷掉，请先登录"})
    if login_user is None:
        return JsonResponse({"status_code": '302', "message": "请先登录"})
    mp = MysqlProxy()
    sql_getpage = 'select page_size from jm_statement.user_profile where `user_id` = %s'
    page_obj = mp.get_one(sql_getpage, [login_user.user_id])

    if not page_obj['page_size']:
        page_size = 10
    else:
        page_size = page_obj['page_size']
    pass
    account_type = request.GET.get("account_type")  # 账户类型
    product_name = request.GET.get("product_name")  # 产品名称
    belong_name = request.GET.get("belong_name")  # 券商名称
    department_name = request.GET.get("department_name")  # 营业部
    end = request.GET.get("end_time")
    sql = "SELECT * FROM jm_statement.account_information ai WHERE ai.`status`='1' and ai.id NOT IN ( SELECT ai.`id` FROM jm_statement.statement_arrive sa INNER JOIN jm_statement.account_information ai ON sa.`id`= ai.`id` WHERE sa.start_date <= %s AND sa.end_date >= %s AND sa.`status`=1 )"

    if account_type != '':
        acc_type_id_list = account_type.split("_")
        type_store_list = cache.get('type_store_list')
        str_col_type_name = generate_multi_select_sql_part(acc_type_id_list, type_store_list)
        sql = sql + " and ai.type in (" + str_col_type_name + ")"

    if product_name != "":
        sql = sql + " and ai.product like " + "'%%" + product_name + "%%'"

    if department_name != "":
        sql = sql + " and ai.business_department like " + "'%%" + department_name + "%%'"

    if belong_name != "":
        belong_name_id_list = str(belong_name).split("_")
        belong_store_list = cache.get('belong_store_list')
        str_col_belong_name = generate_multi_select_sql_part(belong_name_id_list, belong_store_list)
        sql = sql + " and ai.belong in (" + str_col_belong_name + ")"

    pt = ProductT2()
    pt.__int__()
    pt.primary()
    day = datetime.date.strftime(pt.t2day[0]['date'], "%Y-%m-%d")
    if end == "":
        account_info_list = mp.get_list(sql, [day, day])
        end = day
    else:
        account_info_list = mp.get_list(sql, [end, end])
    result_list = list()
    date_end = datetime.datetime.strptime(end,'%Y-%m-%d').date()
    for dict_ele in account_info_list:
        if dict_ele['start_date'] is not None:
            if dict_ele['start_date'] <= date_end:
                result_list.append(dict_ele)
        elif dict_ele['start_date'] is None and dict_ele['status'] == '1':
            result_list.append(dict_ele)
        else:
            print(dict_ele)
    mp.close()
    return JsonResponse(
        {"status_code": '200', "bill_list": result_list, "t2_day": day, "page_size": page_size, "token": token})


def generate_multi_select_sql_part(type_id_list, store_list):
    store_type_name_list = list()  # 存储查询条件列表
    for id in type_id_list:
        for item in store_list:
            if str(item['value']) == id:
                account_type = item['label']
                store_type_name_list.append(account_type)
                break
    str_col_type_name = ''  # 存储符合sql格式要求的查询条件字符串
    for index in range(len(store_type_name_list)):
        if index == len(store_type_name_list) - 1:
            col_type_name = "'" + store_type_name_list[index] + "'"
            str_col_type_name = str_col_type_name + col_type_name
        else:
            col_type_name = "'" + store_type_name_list[index] + "'" + ","
            str_col_type_name = str_col_type_name + col_type_name
    return str_col_type_name


"""
初始化券商和账户类型的下拉列表数据，并以{"value": value, "label": label}形式存入列表，再放到redis缓存中，方便下次查询时候匹配出来label值。
"""


def get_boxs(request):
    sql = "SELECT DISTINCT(belong) FROM account_information"
    sql_1 = "SELECT DISTINCT(type) FROM account_information"
    mp = MysqlProxy()
    belong_list = mp.get_list(sql, None)
    type_list = mp.get_list(sql_1, None)
    belong_store_list = list()
    type_store_list = list()
    for index in range(len(belong_list)):
        value = index
        label = belong_list[index]['belong']
        key_value = {"value": value, "label": label}
        belong_store_list.append(key_value)
    for index in range(len(type_list)):
        value = index
        label = type_list[index]['type']
        key_value = {"value": value, "label": label}
        type_store_list.append(key_value)
    cache.set('belong_store_list', belong_store_list, 60 * 60 * 24)
    cache.set("type_store_list", type_store_list, 60 * 60 * 24)
    mp.close()
    return JsonResponse({"status_code": '200', "belong": belong_store_list, "type_list": type_store_list})


def get_accounts(request):
    mp = MysqlProxy()
    sql = "select * from account_information"
    account_list = mp.get_list(sql, None)
    mp.close()
    for row in account_list:
        for col_key in row:
            if row[col_key] == 'Null' or row[col_key] is None:
                row[col_key] = ''
    return JsonResponse({"status_code": '200', "account_list": account_list})


def insert_account(array):
    for item in range(len(array)):
        if array[item] == '' or array[item] is None:
            array[item] = ''
        else:
            pass
    sql = """insert into jm_statement.account_information (`product`,`belong`,`type`,`account`,`card_sh`,`card_sz`,`start_date`,`business_department`,`contacts`,`contact_email`,`contact_mob`,`contact_tel`,`contact_weixin`,`status`,`trader`,`salesman`,`backstage_staff`,`notes`) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) """
    mp = MysqlProxy()
    id_number = mp.create(sql, array)
    mp.close()
    return id_number


def add_account(request):
    import json, re
    if request.method == 'POST':
        post_body = json.loads(request.body.decode())
        origin_date = post_body['start_date']
        post_body['start_date'] = re.search(r"(\d{4}-\d{1,2}-\d{1,2})", origin_date).group(0)
        if post_body['business_department'] == '' or post_body['business_department'] is None:
            post_body['business_department'] = '暂时未知'
        if post_body['status'] == '' or post_body['status'] is None:
            post_body['status'] = '1'
        index = 0
        account_list = list()
        for ele in post_body:
            account_list.append(post_body[ele])
            index = index + 1
        id_num = insert_account(account_list)
    return JsonResponse({"status_code": '200', "message": '数据录入成功', "id_number": id_num})


def update_account(request):
    """
    sql = update jm_statement.account_information set product = %S, belong=%s,type=%s,account=%s,card_sh=%s,card_sz=%,start_date=%s,end_date=%s,business_department=%s,contacts=%s,contact_email=%s,contact_mob=%s,contact_tel=%s,contact_weixin=%s,`status`=%s,trader=%s,salesman=%s,backstage_staff=%s,notes=%s where id=%s

    """
    import json, re
    if request.method == 'POST':
        post_body = json.loads(request.body.decode())
        index = 0
        be_set_str = ''
        be_set_target = ''
        for ele in post_body:
            if ele == 'end_date':
                origin_date = post_body['end_date']
                print(origin_date)
                if origin_date != '' and origin_date is not None:
                    post_body['end_date'] = re.search(r"(\d{4}-\d{1,2}-\d{1,2})", str(origin_date)).group(0)
            if ele == 'id':
                be_set_target = post_body[ele]
            if ele == 'status':
                if post_body[ele] == '正常':
                    post_body[ele] = 1
                elif post_body[ele] == '销户':
                    post_body[ele] = 0
                elif post_body[ele] == '休眠/冻结':
                    post_body[ele] = 2
                elif post_body[ele] == '准备销户':
                    post_body[ele] = 3
                else:
                    pass
            if post_body[ele] != 'Null' and post_body[ele] != '' and post_body[ele] is not None:
                if ele != 'id':
                    be_set_str += ele + '=' + "'" + str(post_body[ele]) + "'" + ','
            index = index + 1
            print(ele + ":" + str(post_body[ele]))
        be_set_str = be_set_str[:-1]
        sql = "update jm_statement.account_information set " + be_set_str + " where id= " + str(be_set_target)
        print(sql)
        mp = MysqlProxy()
        mp.modify(sql, None)
        mp.close()
    return JsonResponse({"status_code": '200', "message": '数据修改成功'})


def get_account_relate_file(request):
    concat = request.POST
    print(type(concat))
    account_id = concat['account_id']
    mp = MysqlProxy()
    sql = 'select sa.id,sa.account_number,sa.valid_status,ai.product,ai.belong,ai.type from suppose_arrive sa INNER JOIN account_information ai ON sa.account_id = ai.id where sa.account_id = %s'
    file_list = mp.get_list(sql, [account_id])
    print(file_list)
    mp.close()
    return JsonResponse({'status_code': '200', 'message': '查询成功', 'file_list': file_list})


def update_file(request):
    import json
    if request.method == 'POST':
        post_body = json.loads(request.body.decode())
        account_number = post_body['file_name']
        valid_status = post_body['valid_status']
        if valid_status == '有效':
            valid_status = 1
        elif valid_status == '无效':
            valid_status = 0
        file_id = post_body['file_id']
        sql = 'update suppose_arrive set account_number = %s,valid_status=%s  WHERE id = %s'
        mp = MysqlProxy()
        mp.modify(sql, [account_number, valid_status, file_id])
        mp.close()
    return JsonResponse({'status_code': '200', 'message': '修改成功'})


def add_file(request):
    import json
    if request.method == 'POST':
        concat = request.POST
        account_id = concat['account_id']
        account_number = concat['account_number']
        valid_status = concat['valid_status']
    sql = 'insert into jm_statement.suppose_arrive (account_id,account_number,valid_status) VALUES (%s,%s,%s)'
    mp = MysqlProxy()
    auto_id = mp.create(sql, [account_id, account_number, valid_status])
    mp.close()
    return JsonResponse({'status_code': '200', 'message': '新增成功', 'auto_id': auto_id})


# 带出营业部与联系人字符相同的其他相关信息
def get_others_info(request):
    if request.method == 'POST':
        concat = request.POST
        business = concat['business']
        contact = concat['contact']

        sql = 'select contact_email,contact_mob,contact_tel,contact_weixin from jm_statement.account_information WHERE business_department= %s and contacts = %s'
        mp = MysqlProxy()
        contact_result = mp.get_one(sql, [business, contact])  # 没查到结果为None,返回到前端为null

        return JsonResponse({'status_code': '200', 'message': '返回成功啦', 'contact_result': contact_result})


# 检查是否已存在相同产品券商账户
def get_duplicated_account(request):
    if request.method == 'POST':
        concat = request.POST
        product = concat['product']
        belong = concat['belong']
        account_type = concat['type']
        account_number = concat['account']
        sql = 'SELECT id from jm_statement.account_information WHERE product=%s and belong=%s and `type`=%s and account=%s'
        mp = MysqlProxy()
        account_result = mp.get_one(sql, [product, belong, account_type, account_number])
        print(product, belong, account_type, account_number)
        return JsonResponse({'status_code': '200', 'message': '返回成功', 'account_result': account_result})
