# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import Acao
from bagogold.bagogold.models.empresa import Empresa
from bagogold.bagogold.utils.acoes import buscar_ticker_acoes,\
    verificar_tipo_acao
from django.core.management.base import BaseCommand

import re


class Command(BaseCommand):
    help = 'Busca ações existentes na Bovespa que ainda não estejam cadastradas no sistema'

    def handle(self, *args, **options):
        for empresa in Empresa.objects.all():
            tickers = buscar_ticker_acoes('http://bvmf.bmfbovespa.com.br/pt-br/mercados/acoes/empresas/ExecutaAcaoConsultaInfoEmp.asp?CodCVM=%s' % (empresa.codigo_cvm), 1)
            # Filtrar tickers de 3 a 8
            tickers = [ticker for ticker in tickers if int(re.search('\d+', ticker).group(0)) in range(3,9)]
            
            for ticker in tickers:
                if not Acao.objects.filter(ticker=ticker).exists():
                    nova_acao = Acao.objects.create(empresa=empresa, ticker=ticker, tipo=verificar_tipo_acao(ticker))
#                     print 'Criada', nova_acao


# USAR ESSE ENDEREÇO PARA BUSCAR VALORES DIARIOS: https://s.tradingview.com/bovespa/widgetembed/?symbol=EGIE3&interval=1&hidesidetoolbar=0&symboledit=1&saveimage=1&toolbarbg=f1f3f6&editablewatchlist=1&details=1&studies=&widgetbarwidth=300&hideideas=1&theme=White&style=3&timezone=exchange&withdateranges=1&studies_overrides=%7B%7D&overrides=%7B%7D&enabled_features=%5B%5D&disabled_features=%5B%5D&locale=pt&utmsource=www.bmfbovespa.com.br&utmmedium=widget&utmcampaign=chart&utmterm=EGIE3
# OU ESSE: https://s.tradingview.com/bovespa/widgetembed/?symbol=EGIE3&details=1