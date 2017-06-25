# -*- coding: utf-8 -*-
from django.conf.urls import url
import views

urlpatterns = [
    url(r'^listar_moedas/$', views.listar_moedas, name='listar_moedas'),
    ]