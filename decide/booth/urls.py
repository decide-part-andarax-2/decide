from django.urls import path
from .views import BoothView, BoothViewUrl


urlpatterns = [
    path('<int:voting_id>/', BoothView.as_view()),
    path('url/<slug:voting_slug>/', BoothViewUrl.as_view()),
]
