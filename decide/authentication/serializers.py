from rest_framework import serializers
from rest_framework.authtoken.serializers import AuthTokenSerializer

from django.contrib.auth.models import User
from .models import EmailOTPCode, Extra


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'is_staff')

class EmailOTPCodeSerializer(serializers.HyperlinkedModelSerializer):
    email = serializers.EmailField()

    class Meta:
        model = EmailOTPCode
        fields = ('email', 'callback')
        
#Por si se realiza para probar con APIView
class ExtraSerializar(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Extra
        fields = ('id', 'phone', 'totp_code', 'user')

class AuthTokenSecondFactorSerializer(AuthTokenSerializer):
    totp_code = serializers.CharField(label="OTP Code", required=False, default="")

    class Meta:
        fields = ('username', 'password', 'totp_code')