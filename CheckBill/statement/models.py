from django.db import models


# Create your models here.
class Arrive(models.Model):
    start_date = models.DateField('开始日期',auto_now=False, auto_now_add=False,null=True)
    end_date = models.DateField('结束日期',auto_now=False, auto_now_add=False,null=True)
    file_name = models.CharField('文件名',max_length=100,null=False)
    status = models.IntegerField('有效标志',null=True)

    def __str__(self):
        #start = datetime.datetime.strftime(self.start_date,'%Y-%m-%d')
        #end = datetime.datetime.strftime(self.end_date,'%Y-%m-%d')
        return "<Person:{id=%s,start_date=%s,end_date=%s,file_name=%s,status=%d}>" \
               % (self.id, self.start_date.strftime('%Y-%m-%d'), self.end_date.strftime('%Y-%m-%d'),self.status)