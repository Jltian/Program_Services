import json

from django.core.cache import cache
from django.http import JsonResponse

from .models import WX_Login


def login(request):
    global col_token
    username = request.POST.get("username")
    password = request.POST.get("password")
    print("username:"+str(username))
    print("password:"+str(password))
    try:
        user = WX_Login.objects.get(loginname=username)
        print(type(user))
    except:
        date = {'flag': 'no', "msg": "no to user"}
        return JsonResponse({'request': date})
    if password == user.password:
        date_msg = "登陆成功"
        request.session['login_user'] = user
        login_user_token_list = list()
        col_token = str(user.user_id)+"_"+user.loginname+"_"+user.password
        login_user_token_list.append({ col_token : request.session['login_user']})
        print("登录成功后保存session",end="")
        cache.set("login_user",login_user_token_list,60*60*24)
        #print("其id为："+str(request.session['login_user'].user_id))
        #httpresponse = HttpResponse("设置Cookie")
       # httpresponse.set_cookie("login_user",str(request.session['login_user'].user_id))
        date_flag = "yes"
        print("成功")
    else:
        date_msg = "密码输入错误"
        date_flag = "no"

    date = {'flag': date_flag, 'msg': date_msg,'token':col_token}
    user_str = user.__str__()
    user_obj = json.loads(user_str)#把已经编码好的json字符串编码为dict类型的python对象
    print(user_obj)


    user_json = json.dumps(user_obj)#转变成json格式的字符串
    print(user_json)




    return JsonResponse({'request': date,'user_obj':user_str})
    #return httpresponse