# -*- coding: utf-8 -*-
from django.conf import settings

def env(context):
    return {'ENV': settings.ENV}