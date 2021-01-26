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
        widgets = {
            'username': forms.TextInput(attrs={'class':'form-control'}),
            'first_name': forms.TextInput(attrs={'class':'form-control'}),
            'last_name': forms.TextInput(attrs={'class':'form-control'}),
            'email': forms.EmailInput(attrs={'class':'form-control'}),
            'password1': forms.PasswordInput(attrs={'class':'form-control'}),
            'password2': forms.PasswordInput(attrs={'class':'form-control'}),
        }

class ExtraForm(forms.ModelForm):
    base32secret = forms.CharField()

    class Meta:
        model = Extra
        fields = ['phone', 'totp_code']
        widgets = {
            'phone': forms.TextInput(attrs={'class':'form-control'}),
            'totp_code': forms.TextInput(attrs={'class':'form-control'}),
        }

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


class EditUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class':'form-control'}),
            'last_name': forms.TextInput(attrs={'class':'form-control'}),
            'email': forms.EmailInput(attrs={'class':'form-control'}),
        }

    def clean_email(self):
        user_id = self.instance.pk
        email = self.cleaned_data.get('email')
        user_with_email = User.objects.filter(email=email)
        {'pk': user_id} in user_with_email.values('pk')
        
        if user_with_email.exists() and not ({'pk': user_id} in user_with_email.values('pk')):
            raise forms.ValidationError("Email already exists")
        return email

class EditExtraForm(forms.ModelForm):
    class Meta:
        model = Extra
        fields = ['phone']
        widgets = { 'phone': forms.TextInput(attrs={'class':'form-control'}), }
        
    def clean_phone(self):
    #     #Validación del número de teléfono en el formulario extra_form
    #     '''
    #     El número telefónico debe de estar compuesto por 9 dígitos

    #     '''
        phone = self.cleaned_data['phone']
        if (not phone.isdigit()) or len(phone)!=9:
            raise forms.ValidationError('El teléfono debe estar formado por 9 dígitos')
        return phone