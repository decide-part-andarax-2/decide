from rest_framework import parsers, renderers
from authentication.models import EmailOTPCode
from rest_framework.response import Response
from rest_framework.status import (
        HTTP_201_CREATED,
        HTTP_400_BAD_REQUEST,
        HTTP_200_OK,
        HTTP_401_UNAUTHORIZED, 
        HTTP_500_INTERNAL_SERVER_ERROR

)
from  smtplib import SMTPException
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import TemplateView

from .serializers import AuthTokenSecondFactorSerializer, EmailOTPCodeSerializer, UserSerializer
from django.contrib.auth.forms import UserCreationForm
from django.template import RequestContext
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth import logout as auth_logout
from rest_framework.decorators import api_view

from django.urls import reverse
from .serializers import EmailOTPCodeSerializer, UserSerializer
from .email import send_mail_with_token
import pyotp
from django.shortcuts import render, redirect



from .forms import UserForm, ExtraForm, EditUserForm, EditExtraForm
from .models import Extra

def registro_usuario(request, backend='django.contrib.auth.backends.ModelBackend'):
    if request.POST.get("base32secret"):
        base32secret = request.POST.get("base32secret")
    else:
        base32secret = pyotp.random_base32()
    url_totp = pyotp.totp.TOTP(base32secret).provisioning_uri(issuer_name="Decide App")

    user_form = UserForm()
    extra_form = ExtraForm(initial={'base32secret':base32secret})

    if request.method == 'POST':
        extra_form = ExtraForm(request.POST,"extra_form")
        user_form = UserForm(request.POST,"user_form")
        if extra_form.is_valid() and user_form.is_valid():
            user_form.save()
            username = user_form.cleaned_data["username"]
            phone = extra_form.cleaned_data["phone"]
            base32secret = ""
            if extra_form.cleaned_data["totp_code"]:
                base32secret = extra_form.cleaned_data["base32secret"]
            user = User.objects.get(username=username)
            Extra.objects.create(phone=phone, totp_code=base32secret, user=user)
            login(request, user, backend)
            return redirect(to='inicio')
            
    formularios = {
        "user_form":user_form,
        "extra_form":extra_form,
        "url_totp":url_totp,
        "base32secret":base32secret,
    }       
    return render(request, 'registro.html', formularios)

def home(request):
    return render(request, 'index.html')


class GetUserView(APIView):
    def post(self, request):
        key = request.data.get('token', '')
        tk = get_object_or_404(Token, key=key)
        user = UserSerializer(tk.user, many=False)
        return Response(user.data)

class ObtainAuthTokenSecondFactor(APIView):
    throttle_classes = ()
    permission_classes = ()
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = AuthTokenSecondFactorSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        totp_code = serializer.validated_data['totp_code']
        
        try:
            extra = Extra.objects.get(user=user)
        except Extra.DoesNotExist:
            extra = None

        if extra:
            base32secret = extra.totp_code

            if base32secret:
                if not totp_code:
                    return Response({}, status=HTTP_400_BAD_REQUEST)
                current_totp = pyotp.TOTP(base32secret)
                if not current_totp.verify(totp_code):
                    return Response({}, status=HTTP_401_UNAUTHORIZED)

        token, created = Token.objects.get_or_create(user=user)

        return Response({'token': token.key})

class LogoutView(APIView):
    def post(self, request):
        key = request.data.get('token', '')
        try:
            tk = Token.objects.get(key=key)
            tk.delete()
        except ObjectDoesNotExist:
            pass
        return Response({})


class RegisterView(APIView):
    def post(self, request):
        key = request.data.get('token', '')
        tk = get_object_or_404(Token, key=key)
        if not tk.user.is_superuser:
            return Response({}, status=HTTP_401_UNAUTHORIZED)

        username = request.data.get('username', '')
        pwd = request.data.get('password', '')
        if not username or not pwd:
            return Response({}, status=HTTP_400_BAD_REQUEST)

        try:
            user = User(username=username)
            user.set_password(pwd)
            user.save()
            token, _ = Token.objects.get_or_create(user=user)
        except IntegrityError:
            return Response({}, status=HTTP_400_BAD_REQUEST)
        return Response({'user_pk': user.pk, 'token': token.key}, HTTP_201_CREATED)


def github_redirect(request):

    user = request.user
    session_token, created = Token.objects.get_or_create(user=user)
    host = request.get_host()
    scheme = request.is_secure() and "https" or "http"
    base_url = f'{scheme}://{request.get_host()}'
    context = {
        "token":session_token.key,
        "callback":base_url+'/booth/' + str(request.GET.get('next', None)),
        "host":host,
    }
    return render(request, 'github-redirect.html',context)

@api_view(['GET'])
def logoutGitHub(request):
    auth_logout(request)

    if request.user.is_authenticated:
        return Response({}, status=HTTP_400_BAD_REQUEST)
    else:
        return Response({}, status=HTTP_200_OK)



def google_redirect(request):

    user = request.user
    session_token, created = Token.objects.get_or_create(user=user)
    host = request.get_host()
    scheme = request.is_secure() and "https" or "http"
    base_url = f'{scheme}://{request.get_host()}'
    context = {
        "token":session_token.key,
        "callback":base_url+'/booth/' + str(request.GET.get('next', None)),
        "host":host,
    }
    return render(request, 'google-redirect.html',context)




@api_view(['GET'])
def logoutGoogle(request):
    auth_logout(request)

    if request.user.is_authenticated:
        return Response({}, status=HTTP_400_BAD_REQUEST)
    else:
        return Response({}, status=HTTP_200_OK)

def facebook_redirect(request):

    user = request.user
    session_token, created = Token.objects.get_or_create(user=user)
    host = request.get_host()
    scheme = request.is_secure() and "https" or "http"
    base_url = f'{scheme}://{request.get_host()}'
    context = {
        "token":session_token.key,
        "callback":base_url+'/booth/' + str(request.GET.get('next', None)),
        "host":host,
    }
    return render(request, 'facebook-redirect.html',context)


@api_view(['GET'])
def logoutFacebook(request):
    auth_logout(request)

    if request.user.is_authenticated:
        return Response({}, status=HTTP_400_BAD_REQUEST)
    else:
        return Response({}, status=HTTP_200_OK)



class EmailGenerateTokenView(APIView):
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = EmailOTPCodeSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})

        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        callback = serializer.validated_data['callback']

        user = get_object_or_404(User, email=email)
        email_otp_code, created = EmailOTPCode.objects.get_or_create(user=user)


        secret = pyotp.random_base32()

        email_otp_code.callback = callback
        email_otp_code.secret = secret
        email_otp_code.save()

        try:
            totp = pyotp.TOTP(secret, interval=3600)
            token = totp.now()

            host = request.get_host()
            if host == "10.5.0.1:8000":
                host = "localhost:8000"
            scheme = request.is_secure() and "https" or "http"
            link = f'{scheme}://{host}' + reverse("email-confirm-token", None, [str(user.pk), str(token)])
            send_mail_with_token(email, link)
        except SMTPException:
            return Response({}, status=HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({}, status=HTTP_200_OK)


class EmailConfirmTokenView(TemplateView):
    template_name = "authentication/email/confirm-email-token.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        user_id = kwargs.get('userId', '')
        token = kwargs.get('token', '')
        
        context['token'] = ''
        context['callback'] = ''

        if user_id:
            try:
                email_otp_code = EmailOTPCode.objects.get(user__pk=user_id)
                if email_otp_code:
                    totp = pyotp.TOTP(email_otp_code.secret, interval=3600)

                    if totp.verify(token):
                        session_token, created = Token.objects.get_or_create(user=email_otp_code.user)
                        context['token'] = session_token.key
                        context['callback'] = email_otp_code.callback

                email_otp_code.delete()
            except ObjectDoesNotExist:
                pass
            
        return context

def inicio(request):
    
    userLogged = request.user
    try:
        extraLogged = Extra.objects.get(user=userLogged)
    except Extra.DoesNotExist:
        extraLogged = Extra(user=userLogged)
    

    user_form = EditUserForm(instance=userLogged)
    extra_form = EditExtraForm(instance=extraLogged)

    if request.method == 'POST':
        extra_form = EditExtraForm(request.POST,"extra_form", instance=extraLogged)
        user_form = EditUserForm(request.POST,"user_form", instance=userLogged)
        if user_form.is_valid() and extra_form.is_valid():
            user_form.save()
            extra_form.save()
            return redirect(to='inicio')
            
    formularios = {
        "user_form":user_form,
        "extra_form":extra_form,
    }    

    return render(request, 'inicio.html')