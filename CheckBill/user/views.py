from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import HttpResponse
# Create your views here.
from user.models import Profile

from .models import Profile


def add_person(request):
    zhangsan = Profile(user_id=11, user_name='张三', user_phone='13548495217', user_email='zhangsan2551@163.com',
                       is_autorized=1)
    # xu2 = Persion(first_name='徐',last_name='二')
    zhangsan.save()
    # xu2.save()
    # person1 = Persion(first_name='张',last_name='三')
    # person1.save()
    # person2 = Persion()
    # person2.first_name = '李'
    # person2.last_name = '四'
    # person2.save()
    # wangwu = Persion.objects.create(first_name='王',last_name='五')
    # zhaoliu = Persion.objects.get_or_create(first_name='赵',last_name='六')
    return HttpResponse('添加数据成功')


def get_person(request):
    from utils import MysqlProxy
    token = request.GET.get('token')
    print(type(cache.get('login_user')))
    global login_user
    for item in cache.get('login_user'):
        if item[token] != None:
            login_user = item[token]
    if login_user == None:
        return JsonResponse({'status_code': '302', 'message': "请先登录"})
    user_id = login_user.user_id
    mq = MysqlProxy.MysqlProxy()
    user_list = mq.get_list("select * from jm_statement.user_profile where user_id=%s", [int(user_id)])
    print(user_list[0])
    print(type(user_list[0]))
    mq.close()

    return JsonResponse({'status_code': '200', 'user_obj': user_list[0], 'token': token})


def save_pagesize(request):
    global login_user
    from utils import MysqlProxy
    print("==============保存页码==================", end="")
    pagesize = request.GET.get("pagesize")
    login_user_list = cache.get('login_user')
    token = request.GET.get("token")
    for ele in login_user_list:
        if ele[token] != None:
            login_user = ele[token]
    if login_user == None:
        return JsonResponse({'code': '300', 'message': '保存失败，请先登录'})
    user_id = login_user.user_id
    sql = "UPDATE jm_statement.`user_profile` SET `page_size` = %s WHERE `user_id` = %s"
    mq = MysqlProxy.MysqlProxy()
    mq.modify(sql, [int(pagesize), int(user_id)])
    print(pagesize)
    return JsonResponse({'code': '200', 'message': '保存成功', 'token': token})
# def update_person(request):
#     #根据条件查询后再修改和保存
#     # zhangsan = Persion.objects.get(first_name='张')
#     # zhangsan.last_name='三丰'
#     # zhangsan.save()
#     #直接修改所有数据
#     Persion.objects.all().update(first_name='雷')
#     return HttpResponse('修改数据成功')
# def delete_person(request):
#     Persion.objects.get(last_name='三丰').delete()
#     return HttpResponse('数据删除成功')
# def login(request):
#     username = request.POST.get("username")
#     password = request.POST.get("password")
#     print("username:"+str(username))
#     print("password:"+str(password))
#     try:
#         user = Person.objects.get(first_name=username)
#     except:
#         date = {'flag': 'no', "msg": "no to user"}
#         return JsonResponse({'request': date})
#     if password == user.last_name:
#         date_msg = "登陆成功"
#         date_flag = "yes"
#         print("成功")
#     else:
#         date_msg = "密码输入错误"
#         date_flag = "no"
#     date = {'flag': date_flag, 'msg': date_msg}
#
#     return JsonResponse({'request': date})
