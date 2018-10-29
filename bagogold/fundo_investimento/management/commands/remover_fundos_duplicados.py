# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models.functions.base import Length

from bagogold.fundo_investimento.management.commands.preencher_historico_fundo_investimento import formatar_cnpj
from bagogold.fundo_investimento.models import FundoInvestimento, \
    HistoricoValorCotas, OperacaoFundoInvestimento, Administrador


class Command(BaseCommand):
    help = 'TEMPORÁRIO Remover fundos duplicados'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
#                 fundos_desformatados = FundoInvestimento.objects.annotate(text_len=Length('cnpj')).filter(text_len__lte=14)
                
        #         qtd_cnpj_desformatado = len(fundos_desformatados)
        #         
        #         cnpjs_formatados = [formatar_cnpj(fundo.cnpj) for fundo in fundos_desformatados]
        #         
        #         fundos_formatados = FundoInvestimento.objects.filter(cnpj__in=cnpjs_formatados)
        #         
        #         print qtd_cnpj_desformatado, len(fundos_formatados)
        
#                 for fundo_desformatado in fundos_desformatados:
#                     if FundoInvestimento.objects.filter(cnpj=formatar_cnpj(fundo_desformatado.cnpj)).exists():
#                         if HistoricoValorCotas.objects.filter(fundo_investimento=fundo_desformatado).exists() or \
#                             OperacaoFundoInvestimento.objects.filter(fundo_investimento=fundo_desformatado).exists():
#                             # Buscar fundo formatado e apontar para ele
#                             fundo_formatado = FundoInvestimento.objects.get(cnpj=formatar_cnpj(fundo_desformatado.cnpj))
#                             
#                             for historico in HistoricoValorCotas.objects.filter(fundo_investimento=fundo_desformatado):
#                                 historico.fundo_investimento = fundo_formatado
#                                 historico.save()
#                                 
#                             for operacao in OperacaoFundoInvestimento.objects.filter(fundo_investimento=fundo_desformatado):
#                                 operacao.fundo_investimento = fundo_formatado
#                                 operacao.save()
#                             
#                             print 'Dados a serem apagados', fundo_desformatado, \
#                                 HistoricoValorCotas.objects.filter(fundo_investimento=fundo_desformatado).count(), \
#                                 OperacaoFundoInvestimento.objects.filter(fundo_investimento=fundo_desformatado).count()
#                     else:
#                         if HistoricoValorCotas.objects.filter(fundo_investimento=fundo_desformatado).exists() or \
#                             OperacaoFundoInvestimento.objects.filter(fundo_investimento=fundo_desformatado).exists():
#                             print 'Nao existe', fundo_desformatado.cnpj
        
        
        
                admin_desformatados = Administrador.objects.annotate(text_len=Length('cnpj')).filter(text_len__lte=14)
                
        #         qtd_cnpj_desformatado = len(fundos_desformatados)
        #         
        #         cnpjs_formatados = [formatar_cnpj(fundo.cnpj) for fundo in fundos_desformatados]
        #         
        #         fundos_formatados = FundoInvestimento.objects.filter(cnpj__in=cnpjs_formatados)
        #         
        #         print qtd_cnpj_desformatado, len(fundos_formatados)
        
                for admin_desformatado in admin_desformatados:
                    if Administrador.objects.filter(cnpj=formatar_cnpj(admin_desformatado.cnpj)).exists():
                        if FundoInvestimento.objects.filter(administrador=admin_desformatado).exists():
                            # Buscar fundo formatado e apontar para ele
                            admin_formatado = Administrador.objects.get(cnpj=formatar_cnpj(admin_desformatado.cnpj))
                            print FundoInvestimento.objects.filter(administrador=admin_desformatado).count()
                            
                            for fundo in FundoInvestimento.objects.filter(administrador=admin_desformatado):
                                fundo.administrador = admin_formatado
                                fundo.save()
                                
                            print 'Dados a serem apagados', admin_desformatado, \
                                FundoInvestimento.objects.filter(administrador=admin_desformatado).count()
                        else:
                            print 'Sem dados a apagar', admin_desformatado
                        
                        admin_desformatado.delete()
                    else:
                        if FundoInvestimento.objects.filter(administrador=admin_desformatado).exists():
                            print 'Nao existe mas tem fundo vinculado', admin_desformatado.cnpj
                        else:
                            print 'Nao existe', admin_desformatado
                        admin_desformatado.cnpj = formatar_cnpj(admin_desformatado.cnpj)    
                        admin_desformatado.save()
                        
                            
                raise ValueError('TESTE')
        
        except:
            raise