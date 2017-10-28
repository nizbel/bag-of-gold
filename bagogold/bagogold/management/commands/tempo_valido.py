# -*- coding: utf-8 -*-
from bagogold.bagogold.models.gerador_proventos import \
    InvestidorLeituraDocumento, ProventoFIIDocumento, ProventoAcaoDocumento
from decimal import Decimal
from django.core.management.base import BaseCommand
import datetime

class Command(BaseCommand):
    help = 'TEMPORÁRIO verificar o tempo médio que será dado para cada leitura'

    def handle(self, *args, **options):
        leituras = InvestidorLeituraDocumento.objects.filter(data_leitura__date=datetime.date(2017, 10, 20)).order_by('data_leitura')
        for leitura in leituras:
            leitura.tempo_decorrido = (leitura.data_leitura \
                                       - InvestidorLeituraDocumento.objects.filter(data_leitura__lt=leitura.data_leitura).order_by('-data_leitura')[0].data_leitura).seconds
            print leitura, leitura.tempo_decorrido
        leituras_fii = leituras.filter(documento__tipo='F')
        leituras_acao = leituras.filter(documento__tipo='A')
        
        proventos_fii_criados = 0
        tempo_medio_exclusao_fii = 0
        tempo_medio_provento_fii = 0
        for leitura in leituras_fii:
            proventos_fii_criados += ProventoFIIDocumento.objects.filter(documento=leitura.documento).count()
            if leitura.decisao == 'E':
                tempo_medio_exclusao_fii += leitura.tempo_decorrido
            else:
                tempo_medio_provento_fii += leitura.tempo_decorrido
        tempo_medio_exclusao_fii = 0 if leituras_fii.filter(decisao='E').count() == 0 else \
            Decimal(tempo_medio_exclusao_fii) / leituras_fii.filter(decisao='E').count()
        tempo_medio_provento_fii = 0 if proventos_fii_criados == 0 else Decimal(tempo_medio_provento_fii) / proventos_fii_criados
            
        print 'Leituras de FII:', leituras_fii.count(), u'Exclusões:', leituras_fii.filter(decisao='E').count(), \
            'Proventos criados:', proventos_fii_criados
        print u'Tempo médio por exclusão:', tempo_medio_exclusao_fii, u'Tempo médio por provento:', tempo_medio_provento_fii
            
        proventos_acao_criados = 0
        tempo_medio_exclusao_acao = 0
        tempo_medio_provento_acao = 0
        for leitura in leituras_acao:
            proventos_acao_criados += ProventoAcaoDocumento.objects.filter(documento=leitura.documento).count()
            if leitura.decisao == 'E':
                tempo_medio_exclusao_acao += leitura.tempo_decorrido
            else:
                tempo_medio_provento_acao += leitura.tempo_decorrido
        tempo_medio_exclusao_acao = 0 if leituras_acao.filter(decisao='E').count() == 0 else \
            Decimal(tempo_medio_exclusao_acao) / leituras_acao.filter(decisao='E').count()
        tempo_medio_provento_acao = 0 if proventos_acao_criados == 0 else Decimal(tempo_medio_provento_acao) / proventos_acao_criados
        
        print u'Leituras de Ação:', leituras_acao.count(), u'Exclusões:', leituras_acao.filter(decisao='E').count(), \
            'Proventos criados:', proventos_acao_criados
        print u'Tempo médio por exclusão:', tempo_medio_exclusao_acao, u'Tempo médio por provento:', tempo_medio_provento_acao