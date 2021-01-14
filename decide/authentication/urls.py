from django.urls import include, path
from rest_framework.authtoken.views import obtain_auth_token
from django.contrib.auth.decorators import login_required


from .views import GetUserView, LogoutView, RegisterView, EmailGenerateTokenView, EmailConfirmTokenView, registro_usuario, inicio, github_redirect, logoutGitHub, ObtainAuthTokenSecondFactor, google_redirect, logoutGoogle, facebook_redirect, logoutFacebook


urlpatterns = [
    #path('login/', obtain_auth_token),
    path('login/', ObtainAuthTokenSecondFactor.as_view()),
    path('logout/', LogoutView.as_view()),
    path('getuser/', GetUserView.as_view()),
    path('register/', RegisterView.as_view()),
    path('email-generate-token/', EmailGenerateTokenView.as_view()),
    path('email-confirm-token/<userId>/<token>/', EmailConfirmTokenView.as_view(), name="email-confirm-token"),
    path('registro/', registro_usuario),
    path('inicio/', login_required(inicio), name="inicio"),
    path('social-auth/', include('social_django.urls', namespace='social')),
    path('github-redirect',github_redirect),
    path('logoutGithub/',logoutGitHub),
    path('google-redirect',google_redirect),
    path('logoutGoogle/',logoutGoogle),
    path('facebook-redirect',facebook_redirect),
    path('logoutFacebook/',logoutFacebook)


]
