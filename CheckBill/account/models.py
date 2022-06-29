from django.db import models


# Create your models here.
class Information(models.Model):
    product = models.CharField('产品名称', max_length=60, null=False)
    belong = models.CharField('券商', max_length=60, null=True)
    type = models.CharField('账户类型', max_length=60, null=True)
    account = models.CharField('账户号', max_length=60, null=True)
    card_sh = models.CharField('上海卡号', max_length=60, null=True)
    card_sz = models.CharField('深圳卡号', max_length=60, null=True)
    start_date = models.DateField('账户启用日期', null=True)
    end_date = models.DateField('账户销户日期', null=True)
    business_department = models.CharField('所属营业部', max_length=120, null=True)
    contacts = models.CharField('联系人', max_length=60, null=True)
    contact_email = models.CharField('联系邮箱', max_length=60, null=True)
    contact_mob = models.CharField('联系手机', max_length=60, null=True)
    contact_tel = models.CharField('联系电话', max_length=60, null=True)
    contact_weixin = models.CharField('联系微信', max_length=60, null=True)
    status = models.CharField(max_length=60, null=True)
    trader = models.CharField('认领交易员', max_length=60, null=True)
    salesman = models.CharField('认领销售员', max_length=60, null=True)
    backstage_staff = models.CharField('认领后台员', max_length=60, null=True)
    notes = models.CharField('', max_length=255, null=True)

    def __str__(self):
        return "<Information:{id=%d,product=%s,belong=%s,type=%s,account=%s,card_sh=%s,card_sz=%s}>" \
               % (self.id, self.product, self.belong, self.type, self.account, self.card_sh, self.card_sz)
