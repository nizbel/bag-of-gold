# -*- coding: utf-8 -*-
from bagogold.bagogold.models.td import Titulo, OperacaoTitulo, HistoricoTitulo
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'TEMPORÁRIO Verifica integridade dos títulos de Tesouro Direto'

    def add_arguments(self, parser):
        parser.add_argument('--apagar', action='store_true')
        
    def handle(self, *args, **options):
        tipos_titulo = Titulo.objects.all().values_list('tipo', flat=True).distinct()
        for tipo in tipos_titulo:
            lista_tipo_data = list()
            for titulo in Titulo.objects.filter(tipo=tipo).order_by('id'):
                if titulo.data_vencimento  not in lista_tipo_data:
                    lista_tipo_data.append(titulo.data_vencimento)
                else:
                    if options['apagar']:
                        if OperacaoTitulo.objects.filter(titulo=titulo).count() > 0:
                            print u'Não foi possível apagar %s pois já há operação cadastrada' % (titulo)
                        else:
                            titulo.delete()
                    else:
                        print 'Repetido', tipo, titulo.data_vencimento
                        print 'Qtd. Operações', OperacaoTitulo.objects.filter(titulo=titulo).count()
                        print 'Qtd. Histórico', HistoricoTitulo.objects.filter(titulo=titulo).count(), 'vs', \
                            HistoricoTitulo.objects.filter(titulo=Titulo.objects.filter(tipo=tipo, data_vencimento=titulo.data_vencimento) \
                                                           .order_by('id')[0]).count()
                    