# -*- coding: utf-8 -*-
from decimal import Decimal
from django import forms
from django.db import models

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
        for operacao_divisao in DivisaoOperacaoLC.objects.filter(divisao=self):
            operacao = operacao_divisao.operacao
            if operacao.tipo_operacao == 'C':
                saldo -= operacao_divisao.quantidade 
            elif operacao.tipo_operacao == 'V':
                saldo += operacao_divisao.quantidade
                
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