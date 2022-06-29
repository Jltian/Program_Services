from django.db import models
class Profile(models.Model):
    user_id = models.IntegerField()
    user_name = models.CharField(max_length=20)
    user_phone = models.CharField(max_length=20)
    user_email = models.CharField(max_length=30)
    is_autorized = models.IntegerField()
    def __str__(self):
        return '{"user_id"=%d,"user_name"="%s","user_phone"="%s","user_email"="%s","is_authorized"=%d}' \
               % (self.user_id, self.user_name, self.user_phone,self.user_email,self.is_autorized)

# Create your models here.
