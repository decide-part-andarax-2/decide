from rest_framework import serializers

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
        fields = ('id', 'phone', 'double_authentication', 'user')