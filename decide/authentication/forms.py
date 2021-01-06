from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.db import models
from .models import *


class UserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

class ExtraForm(forms.ModelForm):
    class Meta:
        model = Extra
        fields = ['phone', 'double_authentication']

    def clean_phone(self):
        #Validación del número de teléfono en el formulario extra_form
        '''
        El número telefónico debe de estar compuesto por 9 dígitos

        '''
        phone = self.cleaned_data['phone']
        if (not phone.isdigit()) or len(phone)!=9:
            raise forms.ValidationError('El teléfono debe estar formado por 9 dígitos')
        return phone

    

