# -*- coding: utf-8 -*-
from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth.views import login

urlpatterns = [
    # Examples:
    # url(r'^$', 'bagogold.views.home'', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', admin.site.urls),
    
    url(r'^login/$', login, {'template_name': 'login.html'}),
    
    # App bagogold
    url(r'', include('bagogold.bagogold.urls')),
]
