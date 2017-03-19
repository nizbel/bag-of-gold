# -*- coding: utf-8 -*-
from bagogold.bagogold.models.lc import HistoricoTaxaDI, HistoricoTaxaDI
from decimal import Decimal
from django import forms
from django.db import models
from django.db.models.aggregates import Sum
from django.db.models.expressions import Case, When, F
from django.db.models.fields import DecimalField
import datetime

class Divisao (models.Model):
    nome = models.CharField(u'Nome da divisão', max_length=50)
    valor_objetivo = models.DecimalField(u'Objetivo', max_digits=11, decimal_places=2, blank=True, default=0)
    investidor = models.ForeignKey('Investidor')
    
    def __unicode__(self):
        return self.nome
    
    def objetivo_indefinido(self):
        return (self.valor_objetivo == 0)
    
    def divisao_principal(self):
        return self.investidor.divisaoprincipal.divisao.id == self.id

    def possui_operacoes_registradas(self):
        possui_operacoes = (DivisaoOperacaoAcao.objects.filter(divisao=self).count() + DivisaoOperacaoCDB_RDB.objects.filter(divisao=self).count() + DivisaoOperacaoFII.objects.filter(divisao=self).count() + \
            DivisaoOperacaoFundoInvestimento.objects.filter(divisao=self).count() + DivisaoOperacaoLC.objects.filter(divisao=self).count() + DivisaoOperacaoTD.objects.filter(divisao=self).count()) > 0
        
        return possui_operacoes
    
    def saldo_acoes_bh(self, data=datetime.date.today()):
        from bagogold.bagogold.utils.acoes import \
            calcular_poupanca_prov_acao_ate_dia_por_divisao
        """
        Calcula o saldo de operações de ações Buy and Hold de uma divisão (dinheiro livre)
        """
        saldo = Decimal(0)
        for operacao_divisao in DivisaoOperacaoAcao.objects.filter(divisao=self, operacao__destinacao='B', operacao__data__lte=data):
            operacao = operacao_divisao.operacao
            if operacao.tipo_operacao == 'C':
                saldo -= (operacao_divisao.quantidade * operacao.preco_unitario + (operacao.corretagem + operacao.emolumentos - operacao.qtd_proventos_utilizada()) * operacao_divisao.percentual_divisao())
            elif operacao.tipo_operacao == 'V':
                saldo += (operacao_divisao.quantidade * operacao.preco_unitario - (operacao.corretagem + operacao.emolumentos) * operacao_divisao.percentual_divisao())
        
        # Proventos
        saldo += calcular_poupanca_prov_acao_ate_dia_por_divisao(data, self)        
        
        # Transferências
#         for transferencia in TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem='B', data__lte=data):
#             saldo -= transferencia.quantidade
#         for transferencia in TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino='B', data__lte=data):
#             saldo += transferencia.quantidade
            
        saldo += -(TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem='B', data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0) \
            + (TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino='B', data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0)
            
        return saldo
    
    def saldo_acoes_trade(self, data=datetime.date.today()):
        """
        Calcula o saldo de operações de ações para trade de uma divisão (dinheiro livre)
        """
        saldo = Decimal(0)
        for operacao_divisao in DivisaoOperacaoAcao.objects.filter(divisao=self, operacao__destinacao='T', operacao__data__lte=data):
            operacao = operacao_divisao.operacao
            if operacao.tipo_operacao == 'C':
                saldo -= (operacao_divisao.quantidade * operacao.preco_unitario + (operacao.corretagem + operacao.emolumentos) * operacao_divisao.percentual_divisao())
            elif operacao.tipo_operacao == 'V':
                saldo += (operacao_divisao.quantidade * operacao.preco_unitario - (operacao.corretagem + operacao.emolumentos) * operacao_divisao.percentual_divisao())
                
        # Transferências
#         for transferencia in TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem='T', data__lte=data):
#             saldo -= transferencia.quantidade
#         for transferencia in TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino='T', data__lte=data):
#             saldo += transferencia.quantidade

        saldo += -(TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem='T', data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0) \
            + (TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino='T', data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0)
            
        return saldo
    
    def saldo_cdb_rdb(self, data=datetime.date.today()):
        """
        Calcula o saldo de operações de CDB/RDB de uma divisão (dinheiro livre)
        """
        saldo = Decimal(0)
        historico_di = HistoricoTaxaDI.objects.all()
        for operacao_divisao in DivisaoOperacaoCDB_RDB.objects.filter(divisao=self, operacao__data__lte=data):
            operacao = operacao_divisao.operacao
            if operacao.tipo_operacao == 'C':
                saldo -= operacao_divisao.quantidade 
            elif operacao.tipo_operacao == 'V':
                # Para venda, calcular valor da letra no dia da venda
                valor_venda = operacao_divisao.quantidade
                dias_de_rendimento = historico_di.filter(data__gte=operacao.operacao_compra_relacionada().data, data__lt=operacao.data)
                operacao.taxa = operacao.porcentagem()
                for dia in dias_de_rendimento:
                    # Calcular o valor atualizado para cada operacao
                    valor_venda = Decimal((pow((float(1) + float(dia.taxa)/float(100)), float(1)/float(252)) - float(1)) * float(operacao.taxa/100) + float(1)) * valor_venda
                # Arredondar
                str_auxiliar = str(valor_venda.quantize(Decimal('.0001')))
                valor_venda = Decimal(str_auxiliar[:len(str_auxiliar)-2])
                saldo += valor_venda
                
        # Transferências
#         for transferencia in TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem='C', data__lte=data):
#             saldo -= transferencia.quantidade
#         for transferencia in TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino='C', data__lte=data):
#             saldo += transferencia.quantidade
            
        saldo += -(TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem='C', data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0) \
            + (TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino='C', data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0)
            
        return saldo
    
    def saldo_cri_cra(self, data=datetime.date.today()):
        """
        Calcula o saldo de operações de CRI/CRA de uma divisão (dinheiro livre)
        """
        saldo = Decimal(0)
#         historico_di = HistoricoTaxaDI.objects.all()
#         for operacao_divisao in DivisaoOperacaoCDB_RDB.objects.filter(divisao=self, operacao__data__lte=data):
#             operacao = operacao_divisao.operacao
#             if operacao.tipo_operacao == 'C':
#                 saldo -= operacao_divisao.quantidade 
#             elif operacao.tipo_operacao == 'V':
#                 # Para venda, calcular valor da letra no dia da venda
#                 valor_venda = operacao_divisao.quantidade
#                 dias_de_rendimento = historico_di.filter(data__gte=operacao.operacao_compra_relacionada().data, data__lt=operacao.data)
#                 operacao.taxa = operacao.porcentagem()
#                 for dia in dias_de_rendimento:
#                     # Calcular o valor atualizado para cada operacao
#                     valor_venda = Decimal((pow((float(1) + float(dia.taxa)/float(100)), float(1)/float(252)) - float(1)) * float(operacao.taxa/100) + float(1)) * valor_venda
#                 # Arredondar
#                 str_auxiliar = str(valor_venda.quantize(Decimal('.0001')))
#                 valor_venda = Decimal(str_auxiliar[:len(str_auxiliar)-2])
#                 saldo += valor_venda
#                 
#         # Transferências
#         for transferencia in TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem='C', data__lte=data):
#             saldo -= transferencia.quantidade
#         for transferencia in TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino='C', data__lte=data):
#             saldo += transferencia.quantidade
            
        return saldo
    
    def saldo_debentures(self, data=datetime.date.today()):
        """
        Calcula o saldo de operações de Debêntures de uma divisão (dinheiro livre)
        """
        saldo = Decimal(0)
        
        # TODO adicionar pagamentos
                        
        # Transferências
        for transferencia in TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem='E', data__lte=data):
            saldo -= transferencia.quantidade
        for transferencia in TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino='E', data__lte=data):
            saldo += transferencia.quantidade
            
        return saldo
    
    def saldo_fii(self, data=datetime.date.today()):
        from bagogold.bagogold.utils.fii import \
            calcular_poupanca_prov_fii_ate_dia_por_divisao
        """
        Calcula o saldo de operações de FII de uma divisão (dinheiro livre)
        """
        saldo = DivisaoOperacaoFII.objects.filter(divisao=self, operacao__data__lte=data) \
            .annotate(total=Case(When(operacao__tipo_operacao='C', then=-1 * (F('quantidade') * F('operacao__preco_unitario') + (F('operacao__corretagem') + F('operacao__emolumentos')) * (F('quantidade') / F('operacao__quantidade')))),
                            When(operacao__tipo_operacao='V', then=F('quantidade') * F('operacao__preco_unitario') - (F('operacao__corretagem') + F('operacao__emolumentos')) * (F('quantidade') / F('operacao__quantidade'))),
                            output_field=DecimalField())).aggregate(soma_total=Sum('total'))['soma_total'] or Decimal(0)
        
        # Proventos
        saldo += calcular_poupanca_prov_fii_ate_dia_por_divisao(data, self)    
        
        # Transferências
#         for transferencia in TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem='F', data__lte=data):
#             saldo -= transferencia.quantidade
#         for transferencia in TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino='F', data__lte=data):
#             saldo += transferencia.quantidade
        
        saldo += -(TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem='F', data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0) \
            + (TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino='F', data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0)
        
        return saldo
    
    def saldo_fundo_investimento(self, data=datetime.date.today()):
        """
        Calcula o saldo de operações de fundo de investimento de uma divisão (dinheiro livre)
        """
        saldo = Decimal(0)
        for operacao_divisao in DivisaoOperacaoFundoInvestimento.objects.filter(divisao=self, operacao__data__lte=data):
            operacao = operacao_divisao.operacao
            if operacao.tipo_operacao == 'C':
                saldo -= (operacao_divisao.quantidade * operacao.valor_cota())
            elif operacao.tipo_operacao == 'V':
                saldo += (operacao_divisao.quantidade * operacao.valor_cota())
                
        # Transferências
#         for transferencia in TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem='I', data__lte=data):
#             saldo -= transferencia.quantidade
#         for transferencia in TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino='I', data__lte=data):
#             saldo += transferencia.quantidade
        
        saldo += -(TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem='I', data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0) \
            + (TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino='I', data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0)
        
        return saldo
    
    def saldo_lc(self, data=datetime.date.today()):
        """
        Calcula o saldo de operações de Letra de Crédito de uma divisão (dinheiro livre)
        """
        saldo = Decimal(0)
        historico_di = HistoricoTaxaDI.objects.all()
        for operacao_divisao in DivisaoOperacaoLC.objects.filter(divisao=self, operacao__data__lte=data):
            operacao = operacao_divisao.operacao
            if operacao.tipo_operacao == 'C':
                saldo -= operacao_divisao.quantidade 
            elif operacao.tipo_operacao == 'V':
                # Para venda, calcular valor da letra no dia da venda
                valor_venda = operacao_divisao.quantidade
                dias_de_rendimento = historico_di.filter(data__gte=operacao.operacao_compra_relacionada().data, data__lt=operacao.data)
                operacao.taxa = operacao.porcentagem_di()
                for dia in dias_de_rendimento:
                    # Calcular o valor atualizado para cada operacao
                    valor_venda = Decimal((pow((float(1) + float(dia.taxa)/float(100)), float(1)/float(252)) - float(1)) * float(operacao.taxa/100) + float(1)) * valor_venda
                # Arredondar
                str_auxiliar = str(valor_venda.quantize(Decimal('.0001')))
                valor_venda = Decimal(str_auxiliar[:len(str_auxiliar)-2])
                saldo += valor_venda
        
        # Transferências
#         for transferencia in TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem='L', data__lte=data):
#             saldo -= transferencia.quantidade
#         for transferencia in TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino='L', data__lte=data):
#             saldo += transferencia.quantidade
        
        saldo += -(TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem='L', data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0) \
            + (TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino='L', data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0)
        
        return saldo
    
    def saldo_td(self, data=datetime.date.today()):
        """
        Calcula o saldo de operações de Tesouro Direto de uma divisão (dinheiro livre)
        """
        saldo = Decimal(0)
        for operacao_divisao in DivisaoOperacaoTD.objects.filter(divisao=self, operacao__data__lte=data):
            operacao = operacao_divisao.operacao
            if operacao.tipo_operacao == 'C':
                saldo -= (operacao_divisao.quantidade * operacao.preco_unitario + (operacao.taxa_custodia + operacao.taxa_bvmf) * operacao_divisao.percentual_divisao())
            elif operacao.tipo_operacao == 'V':
                saldo += (operacao_divisao.quantidade * operacao.preco_unitario - (operacao.taxa_custodia + operacao.taxa_bvmf) * operacao_divisao.percentual_divisao())
                
        # Transferências
#         for transferencia in TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem='D', data__lte=data):
#             saldo -= transferencia.quantidade
#         for transferencia in TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino='D', data__lte=data):
#             saldo += transferencia.quantidade
        
        saldo += -(TransferenciaEntreDivisoes.objects.filter(divisao_cedente=self, investimento_origem='D', data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0) \
            + (TransferenciaEntreDivisoes.objects.filter(divisao_recebedora=self, investimento_destino='D', data__lte=data).aggregate(qtd_total=Sum('quantidade'))['qtd_total'] or 0)
        
        # Arredondar
        saldo = saldo.quantize(Decimal('.01'))
        
        return saldo
    
    
    def saldo(self, data=datetime.date.today()):
        """
        Calcula o saldo total restante de uma divisão (dinheiro livre)
        """
        saldo = Decimal(0)
        # Ações
        # Buy and hold
        saldo += self.saldo_acoes_bh(data=data)
        # Trades
        saldo += self.saldo_acoes_trade(data=data)
        # CDB/RDB
        saldo += self.saldo_cdb_rdb(data=data)
        # Debêntures
#         saldo += self.saldo_debentures(data=data)
        # FII
        saldo += self.saldo_fii(data=data)
        # Fundo de investimento
        saldo += self.saldo_fundo_investimento(data=data)
        # LC
        saldo += self.saldo_lc(data=data)
        # TD
        saldo += self.saldo_td(data=data)
        
        return saldo
    
class DivisaoPrincipal (models.Model):
    divisao = models.ForeignKey('Divisao')
    investidor = models.OneToOneField('Investidor', on_delete=models.CASCADE, primary_key=True)
    
class DivisaoOperacaoLC (models.Model):
    divisao = models.ForeignKey('Divisao')
    operacao = models.ForeignKey('OperacaoLetraCredito')
    """
    Guarda a quantidade da operação que pertence a divisão
    """
    quantidade = models.DecimalField('Quantidade (em reais)',  max_digits=11, decimal_places=2)
    
    class Meta:
        unique_together=('divisao', 'operacao')
    
    def __unicode__(self):
        return self.divisao.nome + ': ' + str(self.quantidade) + ' de ' + unicode(self.operacao)
    
    """
    Calcula o percentual da operação que foi para a divisão
    """
    def percentual_divisao(self):
        return self.quantidade / self.operacao.quantidade
    
class DivisaoOperacaoCDB_RDB (models.Model):
    divisao = models.ForeignKey('Divisao')
    operacao = models.ForeignKey('OperacaoCDB_RDB')
    """
    Guarda a quantidade da operação que pertence a divisão
    """
    quantidade = models.DecimalField('Quantidade (em reais)',  max_digits=11, decimal_places=2)
    
    class Meta:
        unique_together=('divisao', 'operacao')
    
    def __unicode__(self):
        return self.divisao.nome + ': ' + str(self.quantidade) + ' de ' + unicode(self.operacao)
    
    """
    Calcula o percentual da operação que foi para a divisão
    """
    def percentual_divisao(self):
        return self.quantidade / self.operacao.quantidade
    
class DivisaoOperacaoCRI_CRA (models.Model):
    divisao = models.ForeignKey('Divisao')
    operacao = models.ForeignKey('cri_cra.OperacaoCRI_CRA')
    """
    Guarda a quantidade da operação que pertence a divisão
    """
    quantidade = models.DecimalField('Quantidade (em certificados)',  max_digits=11, decimal_places=2)
     
    class Meta:
        unique_together=('divisao', 'operacao')
     
    def __unicode__(self):
        return self.divisao.nome + ': ' + str(self.quantidade) + ' de ' + unicode(self.operacao)
     
    """
    Calcula o percentual da operação que foi para a divisão
    """
    def percentual_divisao(self):
        return self.quantidade / self.operacao.quantidade
    
class DivisaoOperacaoDebenture (models.Model):
    divisao = models.ForeignKey('Divisao')
    operacao = models.ForeignKey('OperacaoDebenture')
    """
    Guarda a quantidade da operação que pertence a divisão
    """
    quantidade = models.DecimalField('Quantidade (em títulos)',  max_digits=11, decimal_places=2)
    
    class Meta:
        unique_together=('divisao', 'operacao')
    
    def __unicode__(self):
        return self.divisao.nome + ': ' + str(self.quantidade) + ' de ' + unicode(self.operacao)
    
    """
    Calcula o percentual da operação que foi para a divisão
    """
    def percentual_divisao(self):
        return self.quantidade / self.operacao.quantidade
    
class DivisaoOperacaoFundoInvestimento (models.Model):
    divisao = models.ForeignKey('Divisao')
    operacao = models.ForeignKey('OperacaoFundoInvestimento')
    """
    Guarda a quantidade de cotas que pertence a divisão
    """
    quantidade = models.DecimalField('Quantidade (em cotas)',  max_digits=11, decimal_places=2)
    
    class Meta:
        unique_together=('divisao', 'operacao')
    
    def __unicode__(self):
        return self.divisao.nome + ': ' + str(self.quantidade) + ' de ' + unicode(self.operacao)
    
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
    quantidade = models.IntegerField('Quantidade (em ações)')
    
    class Meta:
        unique_together=('divisao', 'operacao')
    
    def __unicode__(self):
        return self.divisao.nome + ': ' + str(self.quantidade) + ' de ' + unicode(self.operacao)
    
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
    quantidade = models.DecimalField(u'Quantidade (em títulos)', max_digits=7, decimal_places=2) 
    
    class Meta:
        unique_together=('divisao', 'operacao')
    
    def __unicode__(self):
        return self.divisao.nome + ': ' + str(self.quantidade) + ' de ' + unicode(self.operacao)
        
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
    quantidade = models.IntegerField('Quantidade (em papéis)')
    
    class Meta:
        unique_together=('divisao', 'operacao')
    
    def __unicode__(self):
        return self.divisao.nome + ': ' + str(self.quantidade) + ' de ' + unicode(self.operacao)
        
    def percentual_divisao(self):
        """
        Calcula o percentual da operação que foi para a divisão
        """
        return self.quantidade / self.operacao.quantidade
    
class TransferenciaEntreDivisoes(models.Model):
    TIPO_INVESTIMENTO_BUY_AND_HOLD = 'B'
    TIPO_INVESTIMENTO_CDB_RDB = 'C'
    TIPO_INVESTIMENTO_TESOURO_DIRETO = 'D'
    TIPO_INVESTIMENTO_DEBENTURE = 'E'
    TIPO_INVESTIMENTO_FII = 'F'
    TIPO_INVESTIMENTO_FUNDO_INV = 'I'
    TIPO_INVESTIMENTO_LCI_LCA = 'L'
    TIPO_INVESTIMENTO_CRI_CRA = 'R'
    TIPO_INVESTIMENTO_TRADING = 'T'
    
    ESCOLHAS_TIPO_INVESTIMENTO = (('', 'Fonte externa'), 
                                  (TIPO_INVESTIMENTO_BUY_AND_HOLD, 'Buy and Hold'), 
                                  (TIPO_INVESTIMENTO_CDB_RDB, 'CDB/RDB'), 
                                  (TIPO_INVESTIMENTO_TESOURO_DIRETO, 'Tesouro Direto'), 
                                  (TIPO_INVESTIMENTO_DEBENTURE, 'Debênture'),
                                  (TIPO_INVESTIMENTO_FII, 'Fundo de Inv. Imobiliário'), 
                                  (TIPO_INVESTIMENTO_FUNDO_INV, 'Fundo de Investimento'),
                                  (TIPO_INVESTIMENTO_LCI_LCA, 'Letras de Crédito'), 
                                  (TIPO_INVESTIMENTO_CRI_CRA, 'CRI/CRA'), 
                                  (TIPO_INVESTIMENTO_TRADING, 'Trading'))
    
    """
    Transferências em dinheiro entre as divisões, cedente ou recebedor nulos significa que
    é uma transferência de dinheiro de/para meio externo
    """
    divisao_cedente = models.ForeignKey('Divisao', blank=True, null=True, related_name='divisao_cedente')
    divisao_recebedora = models.ForeignKey('Divisao', blank=True, null=True, related_name='divisao_recebedora')
    data = models.DateField(u'Data da transferência', blank=True, null=True)
    """
    B = Buy and Hold; C = CDB/RDB; D = Tesouro Direto; E = Debênture; F = FII; 
    I = Fundo de investimento; L = Letra de Crédito; R = CRI/CRA; T = Trading; N = Não alocado
    """
    investimento_origem = models.CharField('Investimento de origem', blank=True, null=True, max_length=1)
    investimento_destino = models.CharField('Investimento de destino', blank=True, null=True, max_length=1)
    """
    Quantidade em R$
    """
    quantidade = models.DecimalField(u'Quantidade transferida', max_digits=11, decimal_places=2)
    descricao = models.CharField(u'Descrição', blank=True, null=True, max_length=150)
    
    def __unicode__(self):
        descricao = ('(' + self.descricao + ')') if self.descricao else ''
        nome_divisao_cedente = self.divisao_cedente.nome if self.divisao_cedente else 'Meio externo'
        nome_divisao_recebedora = self.divisao_recebedora.nome if self.divisao_recebedora else 'Meio externo'
        return 'R$' + str(self.quantidade) + ' de ' + nome_divisao_cedente + ' para ' + nome_divisao_recebedora + ' em ' + str(self.data) + ' ' + descricao
    
    def intradivisao(self):
        """
        Verifica se a transferência foi feita entre investimentos de uma mesma divisão
        """
        return self.divisao_cedente == self.divisao_recebedora
    
    def investimento_origem_completo(self):
        if self.investimento_origem == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_BUY_AND_HOLD:
            return 'Buy and Hold'
        elif self.investimento_origem == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_CDB_RDB:
            return 'CDB/RDB'
        elif self.investimento_origem == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_TESOURO_DIRETO:
            return 'Tesouro Direto'
        elif self.investimento_origem == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_DEBENTURE:
            return 'Debênture'
        elif self.investimento_origem == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_FII:
            return 'FII'
        elif self.investimento_origem == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_FUNDO_INV:
            return 'Fundo de inv.'
        elif self.investimento_origem == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_LCI_LCA:
            return 'Letra de Crédito'
        elif self.investimento_origem == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_CRI_CRA:
            return 'CRI/CRA'
        elif self.investimento_origem == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_TRADING:
            return 'Trading'
        elif self.investimento_origem == 'N':
            return 'Não alocado'
    
    def investimento_destino_completo(self):
        if self.investimento_destino == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_BUY_AND_HOLD:
            return 'Buy and Hold'
        elif self.investimento_destino == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_CDB_RDB:
            return 'CDB/RDB'
        elif self.investimento_destino == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_TESOURO_DIRETO:
            return 'Tesouro Direto'
        elif self.investimento_destino == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_DEBENTURE:
            return 'Debênture'
        elif self.investimento_destino == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_FII:
            return 'FII'
        elif self.investimento_destino == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_FUNDO_INV:
            return 'Fundo de inv.'
        elif self.investimento_destino == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_LCI_LCA:
            return 'Letra de Crédito'
        elif self.investimento_destino == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_CRI_CRA:
            return 'CRI/CRA'
        elif self.investimento_destino == TransferenciaEntreDivisoes.TIPO_INVESTIMENTO_TRADING:
            return 'Trading'
        elif self.investimento_destino == 'N':
            return 'Não alocado'
    
# class EntradaProgramada(models.Model):
#     divisao
#     investimento
#     quantidade
#     frequencia
#     data_inicio
#     data_fim