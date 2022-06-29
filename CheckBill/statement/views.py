import json
import openpyxl
import os

from django.http import JsonResponse


def get_print_bills(request):
    # 处理前端发来的post请求里的print_list
    choice_time = request.GET.get("choice_time")
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = '未到对账单账户信息'
    sheet['A1'] = '产品名称'
    sheet['B1'] = '券商'
    sheet['C1'] = '账户类型'
    sheet['D1'] = '账户号'
    sheet['E1'] = '上海卡号'
    sheet['F1'] = '深圳卡号'
    sheet['G1'] = '开户日期'
    sheet['H1'] = '所属营业部'
    sheet['I1'] = '联系人'
    sheet['J1'] = '邮箱'
    sheet['K1'] = '手机'
    sheet['L1'] = '电话'
    sheet['M1'] = '微信'
    if os.path.exists(choice_time + "未到对账单账户信息.xlsx"):
        os.remove(choice_time + "未到对账单账户信息.xlsx")
    store_list = list()

    # print(choice_time)
    json_str = request.body
    json_dict_list = json.loads(json_str)
    for dl in json_dict_list:
        store_list.append(
            [dl['product'], dl['belong'], dl['type'], dl['account'], dl['card_sh'], dl['card_sz'], dl['start_date'],
             dl['business_department'], dl['contacts'], dl['contact_email'], dl['contact_mob'], dl['contact_tel'],
             dl['contact_weixin']])
    for i in store_list:
        sheet.append(i)
    # datetime.datetime.today().date().strftime("%Y-%m-%d")
    # sub_dir = "frontport/dist/static/"
    sub_dir = "static/"
    # sub_dir_back = "CheckBill/static/"
    sub_dir_front = "frontport/dist/static/"

    save_dir = os.path.join(os.getcwd(), sub_dir_front)
    file_name = "未到对账单账户信息{0}.xlsx".format(choice_time)
    save_unit = save_dir + file_name
    wb.save(save_unit)
    url = "http://192.168.1.31:8000/" + sub_dir + file_name
    # url = 'http://192.168.1.31:8000/'+
    # #applicationnd.openxmlformats-officedocument.spreadsheetml.sheet
    # response = HttpResponse(content=save_virtual_workbook(wb),content_type='applicationnd.openxmlformats-officedocument.spreadsheetml.sheet')
    # # 给返回的文件命名
    # response['Content-Disposition'] = 'attachment; filename={0}.xlsx'.format(quote(str(choice_time+"未到对账单账户信息")))  # 中文名字
    # #syts = os.getcwd()+"\\" +choice_time+"未到对账单账户信息.xlsx"
    # response['urls'] = syts
    # print(syts)
    # JsonResponse({'status':'200','res_url':syts})
    return JsonResponse({'code': 200, 'url': url})

# def get_excel(request):
#     print("66666666666666666")
#     a = "CheckBill/static/"
#     save_path = a + "未到对账单账户信息{0}.xlsx".format("2021-11-01")
#     url = "http://127.0.0.1:8000/"+save_path
#     print(url)
#     response = {
#         'url':url,
#     }
#     return HttpResponse(json.dumps(response))
# def export_data(request):
#
#     wb = openpyxl.Workbook()
# 	'''
# 	....为写入数据的步骤 略
# 	'''
#
# 	# 吧文件流写入 返回体
#     response = HttpResponse(content=save_virtual_workbook(wb),
#                             content_type='applicationnd.openxmlformats-officedocument.spreadsheetml.sheet')
#     # 给返回的文件命名
#     response['Content-Disposition'] = 'attachment; filename={0}.xlsx'.format(quote(str(title)))  # 中文名字
#
#     return response


# def test(request):
#      # 为了使前端获取到Content-Disposition属性
