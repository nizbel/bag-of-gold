# -*- coding: utf-8 -*-
from bagogold.pendencias.utils.investidor import buscar_pendencias_investidor
from django.conf import settings

def env(context):
    return {'ENV': settings.ENV}

def pendencias_investidor(context):
    if not context.user.is_anonymous():
        pendencias = buscar_pendencias_investidor(context.user.investidor)
        num_pendencias = len(pendencias)
        return {'num_pendencias': num_pendencias}
    return {}