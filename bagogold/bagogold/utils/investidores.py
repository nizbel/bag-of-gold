# -*- coding: utf-8 -*-
from django.core.exceptions import PermissionDenied

def is_superuser(user):
    if user.is_superuser:
        return True
    raise PermissionDenied