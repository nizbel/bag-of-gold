# -*- coding: utf-8 -*-
from django.conf.urls import url
import views

urlpatterns = [
    url(r'^post/(?P<post_slug>[\w-]+)/$', views.detalhar_post, name='detalhar_post'),
#     url(r'^historico/$', views.historico, name='historico_criptomoeda'),
    ]