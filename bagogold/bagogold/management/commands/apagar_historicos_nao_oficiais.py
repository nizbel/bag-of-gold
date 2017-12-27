# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import Acao, HistoricoAcao
from bagogold.bagogold.models.fii import FII, HistoricoFII
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Apaga históricos de FII e ações não oficiais'

    def handle(self, *args, **options):
        # Busca o último registro de histórico oficial
        ultima_data_oficial_acao = HistoricoAcao.objects.filter(oficial_bovespa=True).order_by('-data')[0].data
        ultima_data_oficial_fii = HistoricoFII.objects.filter(oficial_bovespa=True).order_by('-data')[0].data
        
        # Apaga registros não oficiais dessa data pra trás
        apagar_historico_acao_nao_oficial_ate_data(ultima_data_oficial_acao)
        apagar_historico_fii_nao_oficial_ate_data(ultima_data_oficial_fii)
            
def apagar_historico_acao_nao_oficial_ate_data(data):
    """
    Apaga histórico de ações que não sejam oficiais até data determinada
    Parâmetros: Data final
    """
    for acao in Acao.objects.all():
        HistoricoAcao.objects.filter(oficial_bovespa=False, data__lte=data, acao=acao).delete()
    
def apagar_historico_fii_nao_oficial_ate_data(data):
    """
    Apaga histórico de FIIs que não sejam oficiais até data determinada
    Parâmetros: Data final
    """
    for fii in FII.objects.all():
        HistoricoFII.objects.filter(oficial_bovespa=False, data__lte=data, fii=fii).delete()