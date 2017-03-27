# -*- coding: utf-8 -*-
from bagogold.pendencias.utils.investidor import buscar_pendencias_investidor
from django.conf import settings
from django.utils import timezone

def env(context):
    return {'ENV': settings.ENV}

def pendencias_investidor(context):
    if not context.user.is_anonymous():
        pendencias = buscar_pendencias_investidor(context.user.investidor)
        for pendencia in pendencias:
            qtd_dias = (timezone.now() - pendencia.data_criacao).days
            if qtd_dias == 0:
                pendencia.texto_data = 'Recente'
            else:
                pendencia.texto_data = ('%s dia' % qtd_dias) if qtd_dias == 1 else ('%s dias' % qtd_dias)
        num_pendencias = len(pendencias)
        return {'num_pendencias': num_pendencias, 'pendencias': pendencias}
    return {}

def breadcrumbs(context):
    return ''