"""CheckBill URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from account import views as account_views
from django.contrib import admin
from django.urls import path, include
from staff import usrl as backport_urls
from statement import views as statement_views
# import index.views
# from user import views
# from account import views
from user import views as user_view

urlpatterns = [
    path('admin', admin.site.urls),
    #path('ahaindex/',views.index),
    #path('add_person/',views.add_person),
    #path('get_information/',views.get_account),
    # path('get_person/',views.get_person),
    #path('',TemplateView.as_view(template_name="index.html")),
    path(r'',include(backport_urls)),
    path('get_users',user_view.get_person),
    path('get_bills',account_views.get_bills),
    path('get_print_bills',statement_views.get_print_bills),
    path('get_boxs',account_views.get_boxs),
    path('save_pagesize',user_view.save_pagesize),
    path('get_accounts',account_views.get_accounts),
    path('add_account',account_views.add_account),
    path('update_account',account_views.update_account),
    path('get_react_files',account_views.get_account_relate_file),
    path('update_file_content',account_views.update_file),
    path('addFile',account_views.add_file),
    path('get_others_info',account_views.get_others_info),
    path('get_duplicated_account',account_views.get_duplicated_account)
    #path('get_excel_bills',statement_views.get_excel)
]
