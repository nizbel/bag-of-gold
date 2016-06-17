# -*- coding: utf-8 -*-
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth.views import login, logout, password_change, password_change_done, \
    password_reset, password_reset_done, password_reset_confirm, password_reset_complete

urlpatterns = [
    # Examples:
    # url(r'^$', 'bagogold.views.home'', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', admin.site.urls),
    
    url(r'^login/$', login, {'template_name': 'login.html'}),
    url(r'^logout/$', logout, {'template_name': 'login.html'}),
    url(r'^password_change/$', password_change, name='password_change'),
    url(r'^password_change/done/$', password_change_done, name='password_change_done'),
    url(r'^password_reset/$', password_reset, name='password_reset'),
    url(r'^password_reset/done/$', password_reset_done, name='password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', password_reset_confirm, name='password_reset_confirm'),
    url(r'^reset/done/$', password_reset_complete, name='password_reset_complete'),
    
    # App bagogold
    url(r'', include('bagogold.bagogold.urls')),
]
