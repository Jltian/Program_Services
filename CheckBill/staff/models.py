from django.db import models
class WX_Login(models.Model):
    user_id = models.IntegerField()
    loginname = models.CharField(max_length=30)
    password = models.CharField(max_length=20)
    app_id = models.CharField(max_length=30)
    app_secret = models.CharField(max_length=30)
    access_token = models.CharField(max_length=30)
    def __str__(self):
        return '{"user_id":%d,"loginname":"%s","password":"%s","app_id":"%s","app_secret":"%s","access_token":"%s"}' \
               % (self.user_id,self.loginname, self.password,self.app_id,self.app_secret,self.access_token)
