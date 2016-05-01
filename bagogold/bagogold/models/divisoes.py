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
    
    
    def saldo_acoes_bh(self):
        """
        Calcula o saldo de operações de ações Buy and Hold de uma divisão (dinheiro livre)
        """
        saldo = Decimal(0)
        for operacao_divisao in DivisaoOperacaoAcao.objects.filter(divisao=self, operacao__destinacao='B'):
            operacao = operacao_divisao.operacao
            if operacao.tipo_operacao == 'C':
                saldo -= (operacao_divisao.quantidade * operacao.preco_unitario + (operacao.corretagem + operacao.emolumentos) * operacao_divisao.percentual_divisao())
            elif operacao.tipo_operacao == 'V':
                saldo += (operacao_divisao.quantidade * operacao.preco_unitario - (operacao.corretagem + operacao.emolumentos) * operacao_divisao.percentual_divisao())
                
        # Transferências
        for transferencia in TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem='B'):
            saldo -= transferencia.quantidade
        for transferencia in TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino='B'):
            saldo += transferencia.quantidade
            
        return saldo
    
    def saldo_acoes_trade(self):
        """
        Calcula o saldo de operações de ações para trade de uma divisão (dinheiro livre)
        """
        saldo = Decimal(0)
        for operacao_divisao in DivisaoOperacaoAcao.objects.filter(divisao=self, operacao__destinacao='T'):
            operacao = operacao_divisao.operacao
            if operacao.tipo_operacao == 'C':
                saldo -= (operacao_divisao.quantidade * operacao.preco_unitario + (operacao.corretagem + operacao.emolumentos) * operacao_divisao.percentual_divisao())
            elif operacao.tipo_operacao == 'V':
                saldo += (operacao_divisao.quantidade * operacao.preco_unitario - (operacao.corretagem + operacao.emolumentos) * operacao_divisao.percentual_divisao())
                
        # Transferências
        for transferencia in TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem='T'):
            saldo -= transferencia.quantidade
        for transferencia in TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino='T'):
            saldo += transferencia.quantidade
            
        return saldo
    
    def saldo_fii(self):
        """
        Calcula o saldo de operações de FII de uma divisão (dinheiro livre)
        """
        saldo = Decimal(0)
        for operacao_divisao in DivisaoOperacaoFII.objects.filter(divisao=self):
            operacao = operacao_divisao.operacao
            if operacao.tipo_operacao == 'C':
                saldo -= (operacao_divisao.quantidade * operacao.preco_unitario + (operacao.corretagem + operacao.emolumentos) * operacao_divisao.percentual_divisao())
            elif operacao.tipo_operacao == 'V':
                saldo += (operacao_divisao.quantidade * operacao.preco_unitario - (operacao.corretagem + operacao.emolumentos) * operacao_divisao.percentual_divisao())
                
        # Transferências
        for transferencia in TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem='F'):
            saldo -= transferencia.quantidade
        for transferencia in TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino='F'):
            saldo += transferencia.quantidade
            
        return saldo
    
    def saldo_lc(self):
        """
        Calcula o saldo de operações de Letra de Crédito de uma divisão (dinheiro livre)
        """
        saldo = Decimal(0)
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
                saldo += valor_venda * operacao_divisao.percentual_divisao()
                
        # Transferências
        for transferencia in TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem='L'):
            saldo -= transferencia.quantidade
        for transferencia in TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino='L'):
            saldo += transferencia.quantidade
            
        return saldo
    
    def saldo_td(self):
        """
        Calcula o saldo de operações de Tesouro Direto de uma divisão (dinheiro livre)
        """
        saldo = Decimal(0)
        for operacao_divisao in DivisaoOperacaoTD.objects.filter(divisao=self):
            operacao = operacao_divisao.operacao
            if operacao.tipo_operacao == 'C':
                saldo -= (operacao_divisao.quantidade * operacao.preco_unitario + (operacao.taxa_custodia + operacao.taxa_bvmf) * operacao_divisao.percentual_divisao())
            elif operacao.tipo_operacao == 'V':
                saldo += (operacao_divisao.quantidade * operacao.preco_unitario - (operacao.taxa_custodia + operacao.taxa_bvmf) * operacao_divisao.percentual_divisao())
            print saldo
                
        # Transferências
        for transferencia in TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem='D'):
            saldo -= transferencia.quantidade
        for transferencia in TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino='D'):
            saldo += transferencia.quantidade
            
        return saldo
    
    
    def saldo(self):
        """
        Calcula o saldo total restante de uma divisão (dinheiro livre)
        """
        saldo = Decimal(0)
        # Ações
        # Buy and hold
        saldo += self.saldo_acoes_bh()
        # Trades
        saldo += self.saldo_acoes_trade()
        # FII
        saldo += self.saldo_fii()
        # LC
        saldo += self.saldo_lc()
        # TD
        saldo += self.saldo_td()
                
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
        
    def percentual_divisao(self):
        """
        Calcula o percentual da operação que foi para a divisão
        """
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
        
    def percentual_divisao(self):
        """
        Calcula o percentual da operação que foi para a divisão
        """
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
    B = Buy and Hold; D = Tesouro Direto; F = FII; L = Letra de Crédito; T = Trading
    """
    investimento_origem = models.CharField('Investimento de origem', blank=True, null=True, max_length=1)
    investimento_destino = models.CharField('Investimento de destino', blank=True, null=True, max_length=1)
    """
    Quantidade em R$
    """
    quantidade = models.DecimalField(u'Quantidade transferida', max_digits=11, decimal_places=2)
    
    def intradivisao(self):
        """
        Verifica se a transferência foi feita entre investimentos de uma mesma divisão
        """
        return self.divisao_cedente == self.divisao_recebedora
    
    