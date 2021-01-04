from authentication.models import EmailOTPCode
from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(Extra)
admin.site.register(EmailOTPCode)

