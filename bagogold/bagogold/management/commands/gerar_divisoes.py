# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import UsoProventosOperacaoAcao, \
    OperacaoAcao
from bagogold.bagogold.models.divisoes import DivisaoPrincipal, Divisao, \
    DivisaoOperacaoAcao, DivisaoOperacaoFII
from bagogold.bagogold.models.fii import UsoProventosOperacaoFII
from bagogold.bagogold.models.investidores import Investidor
from bagogold.bagogold.utils.acoes import calcular_qtd_acoes_ate_dia_por_divisao
from bagogold.bagogold.utils.divisoes import verificar_operacoes_nao_alocadas, \
    preencher_operacoes_div_principal
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Gera divisões e configura como principal para cada usuario'

    def handle(self, *args, **options):
        # Modificar todos os uso proventos para o formato novo
        try:
            for uso_proventos in UsoProventosOperacaoAcao.objects.all():
                uso_proventos.divisao_operacao = DivisaoOperacaoAcao.objects.get(operacao=uso_proventos.operacao)
                uso_proventos.save()
        except:
            pass
        try:
            for uso_proventos in UsoProventosOperacaoFII.objects.all():
                uso_proventos.divisao_operacao = DivisaoOperacaoFII.objects.get(operacao=uso_proventos.operacao)
                uso_proventos.save()
        except:
            pass
        
        # Fazer alterações nos investidores
        for investidor in Investidor.objects.all():
            if not Divisao.objects.filter(investidor=investidor):
                print investidor, 'nao tem divisoes'
                divisao, criado = Divisao.objects.get_or_create(investidor=investidor, nome='Geral')
                DivisaoPrincipal.objects.get_or_create(investidor=investidor, divisao=divisao)
            elif not hasattr(investidor, 'divisaoprincipal'):
                print investidor, 'tem %s divisoes' % (len(Divisao.objects.filter(investidor=investidor))), 'sem principal'
                DivisaoPrincipal.objects.get_or_create(investidor=investidor, divisao=Divisao.objects.filter(investidor=investidor)[0])
            else:
                print investidor, 'tem %s divisoes' % (len(Divisao.objects.filter(investidor=investidor)))
                for divisao in Divisao.objects.filter(investidor=investidor):
                    print divisao, divisao.divisao_principal()

            # Após gerar divisão principal, mudar todas as operações para ela
            for operacao in verificar_operacoes_nao_alocadas(investidor):
                preencher_operacoes_div_principal(operacao)
                
                # Se ainda houver operações de venda não alocadas, alocar verificando a quantidade em cada divisão
                if operacao.tipo_operacao == 'V' and isinstance(operacao, OperacaoAcao):
                    if calcular_qtd_acoes_ate_dia_por_divisao(operacao.data, investidor.divisaoprincipal.divisao.id) >= operacao.quantidade and not DivisaoOperacaoAcao.objects.filter(operacao=operacao):
                        operacao_div_principal = DivisaoOperacaoAcao(operacao=operacao, divisao=investidor.divisaoprincipal.divisao, quantidade=(operacao.quantidade))
                        operacao_div_principal.save()
                    else:
                        print 'Houve um erro nos cálculos'