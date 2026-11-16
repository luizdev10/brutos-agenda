from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path("", views.escolher, name="escolher"),
    path("confirmar/", views.confirmar, name="confirmar"),
    path("agendamento/<int:pk>/", views.resultado, name="resultado"),
    path("agendamento/<int:pk>/cancelar/", views.cancelar, name="cancelar"),
    path("painel/", views.painel, name="painel"),
    path("entrar/", views.LoginComBloqueio.as_view(), name="login"),
    path("sair/", LogoutView.as_view(), name="logout"),
]
