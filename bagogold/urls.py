# -*- coding: utf-8 -*-
from django.conf.urls import include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = [
    # Examples:
    # url(r'^$', 'bagogold.views.home'', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', admin.site.urls),
    
    # App bagogold
    url(r'', include('bagogold.bagogold.urls')),
]
