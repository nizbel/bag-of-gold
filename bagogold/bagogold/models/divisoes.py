# -*- coding: utf-8 -*-
from decimal import Decimal
from django import forms
from django.db import models
from bagogold.bagogold.models.lc import HistoricoTaxaDI

class Divisao (models.Model):
    nome = models.CharField(u'Nome da divisão', max_length=50)
    valor_objetivo = models.DecimalField(u'Objetivo', max_digits=11, decimal_places=2, blank=True, default=0)
    
    def __unicode__(self):
        return self.nome
    
    def objetivo_indefinido(self):
        return (self.valor_objetivo == 0)
    
    def divisao_principal(self):
        # TODO alterar quando adicionar investidor
        try:
            DivisaoPrincipal.objects.get(id=self.id)
            return True
        except DivisaoPrincipal.DoesNotExist:
            return False
    
    """
    Calcula o saldo restante de uma divisão (dinheiro livre)
    """
    def saldo(self):
        saldo = Decimal(0)
        # Ações
        # TODO adicionar trades
        for operacao_divisao in DivisaoOperacaoAcao.objects.filter(divisao=self):
            operacao = operacao_divisao.operacao
            if operacao.tipo_operacao == 'C':
                saldo -= (operacao_divisao.quantidade * operacao.preco_unitario + (operacao.corretagem + operacao.emolumentos) * operacao_divisao.percentual_divisao())
            elif operacao.tipo_operacao == 'V':
                saldo += (operacao_divisao.quantidade * operacao.preco_unitario - (operacao.corretagem + operacao.emolumentos) * operacao_divisao.percentual_divisao())
        
        # FII
        for operacao_divisao in DivisaoOperacaoFII.objects.filter(divisao=self):
            operacao = operacao_divisao.operacao
            if operacao.tipo_operacao == 'C':
                saldo -= (operacao_divisao.quantidade * operacao.preco_unitario + (operacao.corretagem + operacao.emolumentos) * operacao_divisao.percentual_divisao())
            elif operacao.tipo_operacao == 'V':
                saldo += (operacao_divisao.quantidade * operacao.preco_unitario - (operacao.corretagem + operacao.emolumentos) * operacao_divisao.percentual_divisao())
        # LC
        historico_di = HistoricoTaxaDI.objects.all()
        for operacao_divisao in DivisaoOperacaoLC.objects.filter(divisao=self):
            operacao = operacao_divisao.operacao
            if operacao.tipo_operacao == 'C':
                saldo -= operacao_divisao.quantidade 
            elif operacao.tipo_operacao == 'V':
                # Para venda, calcular valor da letra no dia da venda
                valor_venda = operacao_divisao.quantidade
                dias_de_rendimento = historico_di.filter(data__range=[operacao.operacao_compra_relacionada().data, operacao.data])
                operacao.taxa = operacao.porcentagem_di()
                for dia in dias_de_rendimento:
                    # Arredondar na última iteração
                    if (dia.data == dias_de_rendimento[len(dias_de_rendimento)-1].data):
                        str_auxiliar = str(valor_venda.quantize(Decimal('.0001')))
                        valor_venda = Decimal(str_auxiliar[:len(str_auxiliar)-2])
                    else:
                        # Calcular o valor atualizado para cada operacao
                        valor_venda = Decimal((pow((float(1) + float(dia.taxa)/float(100)), float(1)/float(252)) - float(1)) * float(operacao.taxa/100) + float(1)) * valor_venda
                saldo += valor_venda
                
        # TD
        for operacao_divisao in DivisaoOperacaoTD.objects.filter(divisao=self):
            operacao = operacao_divisao.operacao
            if operacao.tipo_operacao == 'C':
                saldo -= (operacao_divisao.quantidade + (operacao.taxa_custodia + operacao.taxa_bvmf) * operacao_divisao.percentual_divisao())
            elif operacao.tipo_operacao == 'V':
                saldo += (operacao_divisao.quantidade - (operacao.taxa_custodia + operacao.taxa_bvmf) * operacao_divisao.percentual_divisao())
                
        return saldo
    
class DivisaoPrincipal (models.Model):
    divisao = models.ForeignKey('Divisao')
    # TODO adicionar ligação com usuario
    
class DivisaoOperacaoLC (models.Model):
    divisao = models.ForeignKey('Divisao')
    operacao = models.ForeignKey('OperacaoLetraCredito')
    """
    Guarda a quantidade da operação que pertence a divisão
    """
    quantidade = models.DecimalField('Quantidade',  max_digits=11, decimal_places=2)
    
    class Meta:
        unique_together=('divisao', 'operacao')
    
    """
    Calcula o percentual da operação que foi para a divisão
    """
    def percentual_divisao(self):
        return self.quantidade / self.operacao.quantidade
    
class DivisaoOperacaoAcao (models.Model):
    divisao = models.ForeignKey('Divisao')
    operacao = models.ForeignKey('OperacaoAcao')
    """
    Guarda a quantidade de ações que pertence a divisão
    """
    quantidade = models.IntegerField('Quantidade')
    
    class Meta:
        unique_together=('divisao', 'operacao')
    
    """
    Calcula o percentual da operação que foi para a divisão
    """
    def percentual_divisao(self):
        return self.quantidade / self.operacao.quantidade
    
class DivisaoOperacaoTD (models.Model):
    divisao = models.ForeignKey('Divisao')
    operacao = models.ForeignKey('OperacaoTitulo')
    """
    Guarda a quantidade de títulos que pertence a divisão
    """
    quantidade = models.DecimalField(u'Quantidade', max_digits=7, decimal_places=2) 
    
    class Meta:
        unique_together=('divisao', 'operacao')
        
    """
    Calcula o percentual da operação que foi para a divisão
    """
    def percentual_divisao(self):
        return self.quantidade / self.operacao.quantidade
    
class DivisaoOperacaoFII (models.Model):
    divisao = models.ForeignKey('Divisao')
    operacao = models.ForeignKey('OperacaoFII')
    """
    Guarda a quantidade de FIIs que pertence a divisão
    """
    quantidade = models.IntegerField('Quantidade')
    
    class Meta:
        unique_together=('divisao', 'operacao')
        
    """
    Calcula o percentual da operação que foi para a divisão
    """
    def percentual_divisao(self):
        return self.quantidade / self.operacao.quantidade
    
class TransferenciaEntreDivisoes(models.Model):
    """
    Transferências em dinheiro entre as divisões, cedente ou recebedor nulos significa que
    é uma transferência de dinheiro de/para meio externo
    """
    divisao_cedente = models.ForeignKey('Divisao', blank=True, null=True, related_name='divisao_cedente')
    divisao_recebedora = models.ForeignKey('Divisao', blank=True, null=True, related_name='divisao_recebedora')
    data = models.DateField(u'Data da transferência', blank=True, null=True)
    """
    Quantidade em R$
    """
    quantidade = models.DecimalField(u'Quantidade transferida', max_digits=11, decimal_places=2)