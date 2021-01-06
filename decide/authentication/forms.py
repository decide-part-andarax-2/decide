from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.db import models
from .models import *

import pyotp

class UserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

class ExtraForm(forms.ModelForm):
    base32secret = forms.CharField()

    class Meta:
        model = Extra
        fields = ['phone', 'totp_code']

    def clean_phone(self):
    #     #Validación del número de teléfono en el formulario extra_form
    #     '''
    #     El número telefónico debe de estar compuesto por 9 dígitos

    #     '''
        phone = self.cleaned_data['phone']
        if (not phone.isdigit()) or len(phone)!=9:
            raise forms.ValidationError('El teléfono debe estar formado por 9 dígitos')
        return phone

    def clean_totp_code(self):
    #      #Validación del totp_code en el formulario extra_form
    #     '''
    #     El codigo totp debe ser el correcto

    #     '''
        base32secret = self.data.get('base32secret')
        current_totp = pyotp.TOTP(base32secret)
        totp_code = self.cleaned_data['totp_code']

        if totp_code:
            if not current_totp.verify(totp_code):
                raise forms.ValidationError('El codigo OTP no es valido')
        return totp_code