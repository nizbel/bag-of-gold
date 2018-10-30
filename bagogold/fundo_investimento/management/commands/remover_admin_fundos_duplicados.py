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
        
                admin_desformatados = Administrador.objects.annotate(text_len=Length('cnpj')).filter(text_len__lte=14)
                
                qtd_cnpj_desformatado = len(admin_desformatados)
                 
                cnpjs_formatados = [formatar_cnpj(admin.cnpj) for admin in admin_desformatados]
                 
                admins_formatados = Administrador.objects.filter(cnpj__in=cnpjs_formatados).count()
                print 'QTD ANTERIOR', qtd_cnpj_desformatado, admins_formatados, Administrador.objects.all().count(), \
                    FundoInvestimento.objects.all().count()
        
                for admin_desformatado in admin_desformatados:
                    if Administrador.objects.filter(cnpj=formatar_cnpj(admin_desformatado.cnpj)).exists():
                        if FundoInvestimento.objects.filter(administrador=admin_desformatado).exists():
                            # Buscar fundo formatado e apontar para ele
                            admin_formatado = Administrador.objects.get(cnpj=formatar_cnpj(admin_desformatado.cnpj))
                            
                            for fundo in FundoInvestimento.objects.filter(administrador=admin_desformatado):
                                fundo.administrador = admin_formatado
                                fundo.save()
                                
#                             print 'Dados a serem apagados', admin_desformatado, \
#                                 FundoInvestimento.objects.filter(administrador=admin_desformatado).count()
                        else:
#                             print 'Sem dados a apagar', admin_desformatado
                            pass
                        
                        admin_desformatado.delete()
                    else:
                        if FundoInvestimento.objects.filter(administrador=admin_desformatado).exists():
#                             print 'Nao existe mas tem fundo vinculado', admin_desformatado.cnpj
                            pass
                        else:
#                             print 'Nao existe', admin_desformatado
                            pass
                        admin_desformatado.cnpj = formatar_cnpj(admin_desformatado.cnpj)    
                        admin_desformatado.save()
                        
                admins_formatados = Administrador.objects.filter(cnpj__in=cnpjs_formatados).count()
                print 'QTD POSTERIOR', admins_formatados, Administrador.objects.all().count(), \
                    FundoInvestimento.objects.all().count()
                
                raise ValueError('TESTE')
        
        except:
            raise