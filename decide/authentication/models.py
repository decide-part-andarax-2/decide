from django.conf import settings
from django.db import models
from django.contrib.auth.models import User

from django.db.models.fields import CharField, URLField, DateTimeField

# Create your models here.
class EmailOTPCode(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, unique=True,
        on_delete=models.CASCADE, verbose_name="User"
    )
    secret = CharField(max_length=32, verbose_name="Secret Key")
    callback = URLField(verbose_name="Callback")
    created = DateTimeField("Created", auto_now_add=True)

    def __str__(self):
        return self.secret

#Extra: Atributos extras para el modelo User
class Extra(models.Model):
    id = models.AutoField(primary_key=True)
    phone = models.CharField(null = False, max_length = 100, verbose_name='Phone',unique=True)
    totp_code = models.CharField(max_length = 50, null=True, blank=True, verbose_name='TOTP Code')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.phone
