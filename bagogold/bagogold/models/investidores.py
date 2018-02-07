# -*- coding: utf-8 -*-
from bagogold.bagogold.models.acoes import OperacaoAcao
from bagogold.bagogold.models.debentures import OperacaoDebenture
from bagogold.bagogold.models.divisoes import Divisao, DivisaoPrincipal
from bagogold.bagogold.models.fii import OperacaoFII
from bagogold.bagogold.models.lc import OperacaoLetraCredito
from bagogold.bagogold.models.td import OperacaoTitulo
from bagogold.cdb_rdb.models import OperacaoCDB_RDB
from bagogold.cri_cra.models.cri_cra import OperacaoCRI_CRA
from bagogold.criptomoeda.models import OperacaoCriptomoeda
from bagogold.fundo_investimento.models import OperacaoFundoInvestimento
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from bagogold.outros_investimentos.models import Investimento
 
class Investidor (models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    corretagem_padrao = models.DecimalField(u'Corretagem padrão', max_digits=5, decimal_places=2, default=0)
    """
    F = valor fixo, P = valor percentual da operação
    """
    tipo_corretagem = models.CharField(u'Tipo de corretagem', max_length=1, default='F')
    auto_atualizar_saldo = models.BooleanField(u'Atualizar saldo automaticamente?', default=False)
    data_ultimo_acesso = models.DateField(u'Último dia de acesso a uma página', blank=True, null=True)
    
    def __unicode__(self):
        return self.user.username
    
    def buscar_data_primeira_operacao(self):
        datas_primeira_operacao = list()
        
        # Preencher com as primeiras datas de operação para cada investimento
        if OperacaoAcao.objects.filter(investidor=self).exists():
            datas_primeira_operacao.append(OperacaoAcao.objects.filter(investidor=self).order_by('data')[0].data)
        if OperacaoCDB_RDB.objects.filter(investidor=self).exists():
            datas_primeira_operacao.append(OperacaoCDB_RDB.objects.filter(investidor=self).order_by('data')[0].data)
        if OperacaoCriptomoeda.objects.filter(investidor=self).exists():
            datas_primeira_operacao.append(OperacaoCriptomoeda.objects.filter(investidor=self).order_by('data')[0].data)
        if OperacaoFII.objects.filter(investidor=self).exists():
            datas_primeira_operacao.append(OperacaoFII.objects.filter(investidor=self).order_by('data')[0].data)
        if OperacaoLetraCredito.objects.filter(investidor=self).exists():
            datas_primeira_operacao.append(OperacaoLetraCredito.objects.filter(investidor=self).order_by('data')[0].data)
        if OperacaoDebenture.objects.filter(investidor=self).exists():
            datas_primeira_operacao.append(OperacaoDebenture.objects.filter(investidor=self).order_by('data')[0].data)
        if OperacaoFundoInvestimento.objects.filter(investidor=self).exists():
            datas_primeira_operacao.append(OperacaoFundoInvestimento.objects.filter(investidor=self).order_by('data')[0].data)
        if OperacaoCRI_CRA.objects.filter(cri_cra__investidor=self).exists():
            datas_primeira_operacao.append(OperacaoCRI_CRA.objects.filter(cri_cra__investidor=self).order_by('data')[0].data)
        if OperacaoTitulo.objects.filter(investidor=self).exists():
            datas_primeira_operacao.append(OperacaoTitulo.objects.filter(investidor=self).order_by('data')[0].data)
        if Investimento.objects.filter(investidor=self).exists():
            datas_primeira_operacao.append(Investimento.objects.filter(investidor=self).order_by('data')[0].data)
        
        return min(datas_primeira_operacao)
    
@receiver(post_save, sender=User, dispatch_uid="usuario_criado")
def create_investidor(sender, instance, created, **kwargs):
    if created:
        """
        Cria investidor para cada usuário criado
        """
        investidor, criado = Investidor.objects.get_or_create(user=instance)
        """ 
        Cria uma divisão e configura como principal
        """
        divisao, criado = Divisao.objects.get_or_create(investidor=investidor, nome='Geral')
        DivisaoPrincipal.objects.get_or_create(investidor=investidor, divisao=divisao)
        
class LoginIncorreto (models.Model):
    user = models.ForeignKey(User)
    horario = models.DateTimeField(u'Horário')
