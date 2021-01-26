from smtplib import SMTPException

from django.core.mail.message import EmailMultiAlternatives
from authentication.models import EmailOTPCode
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.test import APITestCase
from unittest import mock

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

from django.core import mail
from base.tests import BaseTestCase
from freezegun import freeze_time
import pyotp

from base import mods

from .forms import UserForm, ExtraForm, EditUserForm, EditExtraForm
from .models import Extra
from django.test import Client
from django.test.client import RequestFactory

class AuthTestCase(APITestCase):

    def setUp(self):
        self.client = APIClient()
        mods.mock_query(self.client)
        self.u = User(username='voter1')
        self.u.set_password('123')
        self.u.email = 'voter1@gmail.com'
        self.u.save()

        self.u2fa = User(username='user2fa')
        self.u2fa.set_password('123')
        self.u2fa.email = 'user2fa@gmail.com'
        self.u2fa.save()
        extra2fa = Extra(phone='882277336')
        extra2fa.totp_code = 'S3K3TPI5MYA2M67V'
        extra2fa.user = self.u2fa
        extra2fa.save()

        u2 = User(username='admin')
        u2.set_password('admin')
        u2.is_superuser = True
        u2.save()

    def tearDown(self):
        self.client = None

    def test_login(self):
        data = {'username': 'voter1', 'password': '123'}
        response = self.client.post('/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)

        token = response.json()
        self.assertTrue(token.get('token'))

    def test_login_2fa(self):
        base32secret = 'S3K3TPI5MYA2M67V'
        totp_code = pyotp.TOTP(base32secret).now()
        data = {'username': 'user2fa', 'password': '123', 'totp_code':totp_code}
        response = self.client.post('/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)

        token = response.json()
        self.assertTrue(token.get('token'))

    def test_login_fail(self):
        data = {'username': 'voter1', 'password': '321'}
        response = self.client.post('/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 400)

    def test_login_fail_bad_totp(self):
        data = {'username': 'user2fa', 'password': '123', 'totp_code':'error'}
        response = self.client.post('/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 401)

    def test_getuser(self):
        data = {'username': 'voter1', 'password': '123'}
        response = self.client.post('/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)
        token = response.json()

        response = self.client.post('/authentication/getuser/', token, format='json')
        self.assertEqual(response.status_code, 200)

        user = response.json()
        self.assertEqual(user['id'], self.u.pk)
        self.assertEqual(user['username'], 'voter1')

    def test_getuser_2fa(self):
        base32secret = 'S3K3TPI5MYA2M67V'
        totp_code = pyotp.TOTP(base32secret).now()
        data = {'username': 'user2fa', 'password': '123', 'totp_code':totp_code}
        response = self.client.post('/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)
        token = response.json()

        response = self.client.post('/authentication/getuser/', token, format='json')
        self.assertEqual(response.status_code, 200)

        user = response.json()
        self.assertEqual(user['id'], self.u2fa.pk)
        self.assertEqual(user['username'], 'user2fa')

    def test_getuser_invented_token(self):
        token = {'token': 'invented'}
        response = self.client.post('/authentication/getuser/', token, format='json')
        self.assertEqual(response.status_code, 404)

    def test_getuser_invalid_token(self):
        data = {'username': 'voter1', 'password': '123'}
        response = self.client.post('/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Token.objects.filter(user__username='voter1').count(), 1)

        token = response.json()
        self.assertTrue(token.get('token'))

        response = self.client.post('/authentication/logout/', token, format='json')
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/authentication/getuser/', token, format='json')
        self.assertEqual(response.status_code, 404)

    def test_logout(self):
        data = {'username': 'voter1', 'password': '123'}
        response = self.client.post('/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Token.objects.filter(user__username='voter1').count(), 1)

        token = response.json()
        self.assertTrue(token.get('token'))

        response = self.client.post('/authentication/logout/', token, format='json')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(Token.objects.filter(user__username='voter1').count(), 0)

    def test_register_bad_permissions(self):
        data = {'username': 'voter1', 'password': '123'}
        response = self.client.post('/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)
        token = response.json()

        token.update({'username': 'user1'})
        response = self.client.post('/authentication/register/', token, format='json')
        self.assertEqual(response.status_code, 401)

    def test_register_bad_request(self):
        data = {'username': 'admin', 'password': 'admin'}
        response = self.client.post('/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)
        token = response.json()

        token.update({'username': 'user1'})
        response = self.client.post('/authentication/register/', token, format='json')
        self.assertEqual(response.status_code, 400)

    def test_register_user_already_exist(self):
        data = {'username': 'admin', 'password': 'admin'}
        response = self.client.post('/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)
        token = response.json()

        token.update(data)
        response = self.client.post('/authentication/register/', token, format='json')
        self.assertEqual(response.status_code, 400)

    def test_register(self):
        data = {'username': 'admin', 'password': 'admin'}
        response = self.client.post('/authentication/login/', data, format='json')
        self.assertEqual(response.status_code, 200)
        token = response.json()

        token.update({'username': 'user1', 'password': 'pwd1'})
        response = self.client.post('/authentication/register/', token, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            sorted(list(response.json().keys())),
            ['token', 'user_pk']
        )

    #Generación exitosa de un token por email
    def test_generate_email_token(self):
        data = {'email': 'voter1@gmail.com', 'callback': 'http://domain.es/callback'}
        response = self.client.post('/authentication/email-generate-token/', data, format='json')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(EmailOTPCode.objects.filter(user__username='voter1').count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    #Comprobación de que el email se ha enviado correctamente
    def test_generate_email_token_send_email(self):
        data = {'email': 'voter1@gmail.com', 'callback': 'http://domain.es/callback'}
        response = self.client.post('/authentication/email-generate-token/', data, format='json')
        self.assertEqual(response.status_code, 200)

        self.assertEqual(EmailOTPCode.objects.filter(user__username='voter1').count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Decide - Correo para autenticación')
        self.assertEqual(len(mail.outbox[0].to), 1)
        self.assertEqual(mail.outbox[0].to[0], 'voter1@gmail.com')

    #Comprobación de que solo puede haber un token funcional por usuario
    def test_generate_email_token_twice(self):
        data = {'email': 'voter1@gmail.com', 'callback': 'http://domain.es/callback'}
        response = self.client.post('/authentication/email-generate-token/', data, format='json')
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/authentication/email-generate-token/', data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(EmailOTPCode.objects.filter(user__username='voter1').count(), 1)
        self.assertEqual(len(mail.outbox), 2)

    #El campo de usuario es obligatorio
    def test_generate_email_token_empty_email(self):
        data = {'email': '', 'callback': 'http://dominio.prueba/callback'}
        response = self.client.post('/authentication/email-generate-token/', data, format='json')
        self.assertEqual(response.status_code, 400)

        self.assertEqual(EmailOTPCode.objects.filter(user__username='voter1').count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    #El campo de callback es obligatorio
    def test_generate_email_token_empty_callback(self):
        data = {'email': 'voter1@gmail.com', 'callback': ''}
        response = self.client.post('/authentication/email-generate-token/', data, format='json')
        self.assertEqual(response.status_code, 400)

        self.assertEqual(EmailOTPCode.objects.filter(user__username='voter1').count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    #El campo de email debe existir para algún usuario
    def test_generate_email_token_wrong_email(self):
        data = {'email': 'no_email@gmail.com', 'callback': 'http://dominio.prueba/callback'}
        response = self.client.post('/authentication/email-generate-token/', data, format='json')
        self.assertEqual(response.status_code, 404)

        self.assertEqual(EmailOTPCode.objects.filter(user__username='voter1').count(), 0)
        self.assertEqual(len(mail.outbox), 0)
    
    #El campo de emmail debe sear adecuado
    def test_generate_email_token_invalid_email(self):
        data = {'email': 'no_email', 'callback': 'http://dominio.prueba/callback'}
        response = self.client.post('/authentication/email-generate-token/', data, format='json')
        self.assertEqual(response.status_code, 400)

        self.assertEqual(EmailOTPCode.objects.filter(user__username='voter1').count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    #El campo de callback debe tratarse de una URL válida
    def test_generate_email_token_wrong_callback(self):
        data = {'email': 'voter1@gmail.com', 'callback': 'no_es_url'}
        response = self.client.post('/authentication/email-generate-token/', data, format='json')
        self.assertEqual(response.status_code, 400)

        self.assertEqual(EmailOTPCode.objects.filter(user__username='voter1').count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    #Cuando el servidor de correo no funcione el servidor debe responder adecuadamente
    def test_generate_email_token_mail_server_not_working(self):
        data = {'email': 'voter1@gmail.com', 'callback': 'http://dominio.prueba/callback'}
        
        with mock.patch.object(EmailMultiAlternatives, 'send') as mock_method:
            mock_method.side_effect = SMTPException()

            response = self.client.post('/authentication/email-generate-token/', data, format='json')
            self.assertEqual(response.status_code, 500)

        self.assertEqual(EmailOTPCode.objects.filter(user__username='voter1').count(), 1)
        self.assertEqual(len(mail.outbox), 0)

class FormTestCase(TestCase):

    #Formato válido campos usuario
    def test_user_form_correct(self):
        form_data = {'username': 'test1', 'first_name': 'Test1', 'last_name': 'Test1', 'email':'test1@gmail.com', 'password1': 'hola1234', 'password2': 'hola1234'}
        form = UserForm(data=form_data)
        self.assertTrue(form.is_valid())

    #La contraseña de verificación es incorrecta
    def test_user_form_incorrect_passwords(self):
        form_data = {'username': 'test1', 'first_name': 'Test1', 'last_name': 'Test1', 'email':'test1@gmail.com', 'password1': 'hola1234', 'password2': 'adios1234'}
        form = UserForm(data=form_data)
        self.assertFalse(form.is_valid())

    #El formato de la contraseña es incorrecta  
    def test_user_form_incorrect__format_password(self):
        form_data = {'username': 'test1', 'first_name': 'Test1', 'last_name': 'Test1', 'email':'test1@gmail.com', 'password1': 'hola', 'password2': 'hola'}
        form = UserForm(data=form_data)
        self.assertFalse(form.is_valid())

    #Username vacío 
    def test_user_form_blank_username(self):
        form_data = {'username': '', 'first_name': 'Test1', 'last_name': 'Test1', 'email':'test1@gmail.com', 'password1': 'hola1234', 'password2': 'hola1234'}
        form = UserForm(data=form_data)
        self.assertFalse(form.is_valid())

    #Password vacía
    def test_user_form_blank_password(self):
        form_data = {'username': 'test1', 'first_name': 'Test1', 'last_name': 'Test1', 'email':'test1@gmail.com', 'password1': '', 'password2': ''}
        form = UserForm(data=form_data)
        self.assertFalse(form.is_valid())

    #Formato válido campos extra
    def test_extra_form_correct(self):
        base32secret = pyotp.random_base32()
        totp_code = pyotp.TOTP(base32secret).now()
        form_data = {'phone':'999999999', 'totp_code':totp_code, 'base32secret':base32secret}
        form = ExtraForm(data=form_data)
        self.assertTrue(form.is_valid())

    #Formato válido campos extra sin codigo totp
    def test_extra_form_correct_nototp(self):
        base32secret = pyotp.random_base32()
        form_data = {'phone':'999999999', 'totp_code':'', 'base32secret':base32secret}
        form = ExtraForm(data=form_data)
        self.assertTrue(form.is_valid())

    #Formato incorrecto teléfono (menos de 9 digitos)
    def test_extra_form_incorrect_less_digits(self):
        base32secret = pyotp.random_base32()
        totp_code = pyotp.TOTP(base32secret).now()
        form_data = {'phone':'123', 'totp_code':totp_code, 'base32secret':base32secret}
        form = ExtraForm(data=form_data)
        self.assertFalse(form.is_valid())

    #Formato incorrecto teléfono (más de 9 digitos)
    def test_extra_form_incorrect_more_digits(self):
        base32secret = pyotp.random_base32()
        totp_code = pyotp.TOTP(base32secret).now()
        form_data = {'phone':'1234567895', 'totp_code':totp_code, 'base32secret':base32secret}
        form = ExtraForm(data=form_data)
        self.assertFalse(form.is_valid())

    #Formato incorrecto teléfono (caracteres que no son digitos)
    def test_extra_form_incorrect_char(self):
        base32secret = pyotp.random_base32()
        totp_code = pyotp.TOTP(base32secret).now()
        form_data = {'phone':'123lopujk', 'totp_code':totp_code, 'base32secret':base32secret}
        form = ExtraForm(data=form_data)
        self.assertFalse(form.is_valid())

    #Campo telefono vacío
    def test_extra_form_incorrect_blank_phone(self):
        base32secret = pyotp.random_base32()
        totp_code = pyotp.TOTP(base32secret).now()
        form_data = {'phone':'', 'totp_code':totp_code, 'base32secret':base32secret}
        form = ExtraForm(data=form_data)
        self.assertFalse(form.is_valid())

    #Codigo totp incorrecto
    def test_extra_form_incorrect_totp(self):
        base32secret = pyotp.random_base32()
        form_data = {'phone':'827364018', 'totp_code':'error', 'base32secret':base32secret}
        form = ExtraForm(data=form_data)
        self.assertFalse(form.is_valid())

class ExtraModel(TestCase):

    #Creación del modelo extra correctamente y su metodo string
    def test_extra_str(self):
        u = User(username='voter1')
        u.set_password('123')
        u.save()
        extra = Extra.objects.create(phone='123456789', totp_code='S3K3TPI5MYA2M67V', user=u)
        self.assertEqual(str(extra), "123456789")

    #Creación del modelo extra correctamente, comprobando que el valor de sus atributos es correcto tras su creación
    def test_extra_valor_campos(self):
        u = User(username='voter1')
        u.set_password('123')
        u.save()
        extra = Extra.objects.create(phone='123456789', totp_code='S3K3TPI5MYA2M67V', user=u)
        self.assertEqual(extra.phone, "123456789")
        self.assertEqual(extra.totp_code, 'S3K3TPI5MYA2M67V')
        self.assertEqual(extra.user, u)


class EditUserFormTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        mods.mock_query(self.client)
        self.u1 = User(username='voter1')
        self.u1.set_password('123')
        self.u1.email = 'voter1@gmail.com'
        self.u1.save()

        self.u2 = User(username='voter2')
        self.u2.set_password('123')
        self.u2.email = 'voter2@gmail.com'
        self.u2.save()
        
    #Formato válido campos usuario
    def test_edit_user_form_correct(self):
        form_data = {'first_name': 'Test1', 'last_name': 'Test1', 'email':'test1@gmail.com'}
        form = EditUserForm(data=form_data)
        self.assertTrue(form.is_valid())

    #Formato válido campos usuario
    def test_edit_user_form_correct_with_empty_fields(self):
        form_data = {'first_name': '', 'last_name': '', 'email':''}
        form = EditUserForm(data=form_data)
        self.assertTrue(form.is_valid())

    #Formato inválido para campo de correo electrónico (email ya exitente) 
    def test_edit_user_form_with_existing_email(self):
        form_data = {'first_name': 'Test1', 'last_name': 'Test1', 'email':'voter1@gmail.com'}
        form = EditUserForm(instance=self.u2, data=form_data)
        self.assertFalse(form.is_valid())
    
    #Formato válido para campo de correo electrónico (email del propio usuario) 
    def test_edit_user_form_without_updating_email(self):
        form_data = {'first_name': 'Test1', 'last_name': 'Test1', 'email':'voter1@gmail.com'}
        form = EditUserForm(instance=self.u1, data=form_data)
        self.assertTrue(form.is_valid())

    #Formato inválido para campo de correo electrónico
    def test_edit_user_form_with_invalid_email(self):
        form_data = {'first_name': 'Test1', 'last_name': 'Test1', 'email':'voter1'}
        form = EditUserForm(instance=self.u1, data=form_data)
        self.assertFalse(form.is_valid())


class EditExtraFormTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        mods.mock_query(self.client)
        self.u1 = User(username='voter1')
        self.u1.set_password('123')
        self.u1.email = 'voter1@gmail.com'
        self.u1.save()

        self.e1 = Extra(user=self.u1)
        self.e1.phone = 666666666
        self.e1.save()

        self.u2 = User(username='voter2')
        self.u2.set_password('123')
        self.u2.email = 'voter2@gmail.com'
        self.u2.save()

        self.e2 = Extra(user=self.u2)
        self.e2.phone = 666666662
        self.e2.save()
        
    #Formato válido campos de extra
    def test_edit_extra_form_correct(self):
        form_data = {'phone': '666666661'}
        form = EditExtraForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    #Formato inválido de teléfono (logitud incorrecta)
    def test_edit_extra_form_with_email_with_different_length(self):
        form_data = {'phone': '66666666666661'}
        form = EditExtraForm(data=form_data)
        self.assertFalse(form.is_valid())

    #Formato inválido de teléfono (no está formado por dígitos)
    def test_edit_extra_form_with_email_without_digits(self):
        form_data = {'phone': 'no_digits'}
        form = EditExtraForm(data=form_data)
        self.assertFalse(form.is_valid())

    #Formato inválido de teléfono (ya usado por otro usuario)
    def test_edit_user_form_with_exiting_phone(self):
        form_data = {'phone': '666666662'}
        form = EditExtraForm(instance=self.e1, data=form_data)
        self.assertFalse(form.is_valid())

    #Formato válido de teléfono (sin modificarlo)
    def test_edit_user_form_without_updating_phone(self):
        form_data = {'phone': '666666666'}
        form = EditExtraForm(instance=self.e1, data=form_data)
        self.assertTrue(form.is_valid())