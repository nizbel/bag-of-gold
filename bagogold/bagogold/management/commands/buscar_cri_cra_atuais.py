# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import Acao
from bagogold.bagogold.models.empresa import Empresa
from bagogold.bagogold.utils.acoes import buscar_ticker_acoes, \
    verificar_tipo_acao
from django.core.management.base import BaseCommand
import re
import urllib
import urllib2



class Command(BaseCommand):
    help = 'Busca os CRI e CRA atualmente válidos'

    def handle(self, *args, **options):
        # Buscar CRIs
        endereco_cri = 'https://www.cetip.com.br/tituloscri'
