# -*- coding: utf-8 -*-
from decimal import Decimal
from django.db import models

class Debenture (models.Model):
    TIPOS_INDICE = ((1, 'Prefixado'),
                    (2, 'IPCA'),
                    (3, 'DI'),
                    (4, 'IGP-M'),
                    (5, 'SELIC'),)
    
    codigo = models.CharField(u'Código', max_length=10)
    """
    1 = Prefixado, 2 = IPCA, 3 = DI, 4 = IGP-M, 5 = SELIC
    """
    indice = models.PositiveSmallIntegerField(u'Índice', choices=TIPOS_INDICE)
    porcentagem = models.DecimalField(u'Porcentagem sobre índice', decimal_places=3, max_digits=6, default=Decimal('100'))
    data_emissao = models.DateField(u'Data de emissão')
    valor_emissao = models.DecimalField(u'Valor nominal na emissão', max_digits=17, decimal_places=8)
    data_inicio_rendimento = models.DateField(u'Data de início do rendimento')
    data_vencimento = models.DateField(u'Data de vencimento', null=True, blank=True)
    data_fim = models.DateField(u'Data de fim', null=True, blank=True)
    incentivada = models.BooleanField(u'É incentivada?')
    padrao_snd = models.BooleanField(u'É padrão SND?')
    
    class Meta:
        unique_together=('codigo', )
    
    def __unicode__(self):
        return self.codigo
    
    def buscar_codigo_tipo_indice(self, nome_indice):
        for indice in [indice for indice in self.TIPOS_INDICE]:
            if indice[1] == nome_indice:
                return indice[0]
        return -1
    
    def buscar_descricao_tipo_indice(self, codigo_indice):
        for indice in [indice for indice in self.TIPOS_INDICE]:
            if indice[0] == codigo_indice:
                return indice[1]
        return ''
    
    def indexacao(self):
        descricao_tipo_indice = self.buscar_descricao_tipo_indice(self.indice)
        if self.buscar_descricao_tipo_indice(self.indice) > -1:
            if descricao_tipo_indice != '' and self.porcentagem == 0:
                self.porcentagem = Decimal(100)
            self.porcentagem = str(self.porcentagem).replace('.', ',').replace(',00', '')
            return '%s%% do %s' % (self.porcentagem, descricao_tipo_indice)
        return ''
    
class AmortizacaoDebenture (models.Model):
    TIPOS_AMORTIZACAO = ((0, u'Indefinido'),
                         (1, u'Percentual fixo sobre o valor nominal atualizado em períodos não uniformes'),
                         (2, u'Percentual fixo sobre o valor nominal atualizado em períodos uniformes'),
                         (3, u'Percentual fixo sobre o valor nominal de emissão em períodos não uniformes'),
                         (4, u'Percentual fixo sobre o valor nominal de emissão em períodos uniformes'),
                         (5, u'Percentual variável sobre o valor nominal atualizado em períodos não uniformes'),
                         (6, u'Percentual variável sobre o valor nominal atualizado em períodos uniformes'),
                         (7, u'Percentual variável sobre o valor nominal de emissão em períodos não uniformes'),
                         (8, u'Percentual variável sobre o valor nominal de emissão em períodos uniformes'),)
    
    debenture = models.OneToOneField('Debenture', on_delete=models.CASCADE, primary_key=True)
    taxa = models.DecimalField(u'Taxa', max_digits=7, decimal_places=4)
    periodo = models.IntegerField(u'Período')
    unidade_periodo = models.CharField(u'Unidade do período', max_length=10)
    carencia = models.DateField(u'Carência', blank=True, null=True)
    tipo = models.PositiveSmallIntegerField(u'Tipo de amortização', choices=TIPOS_AMORTIZACAO)
    data = models.DateField(u'Data')
    
    def descricao(self):
        self.carencia = '' if not self.carencia else self.carencia.strftime('%d/%m/%Y')
        if self.taxa > 0:
            self.taxa = str(self.taxa).replace('.', ',')
            return '%s%% a cada %s %s, a partir de %s' % (self.taxa, self.periodo, self.descricao_unidade_periodo(), self.carencia)
        else:
            if self.tipo >= 5:
                return 'Variável a cada %s %s, a partir de %s' % (self.periodo, self.descricao_unidade_periodo(), self.carencia)
        return 'Não sei'
    
    def descricao_unidade_periodo(self):
        if self.unidade_periodo == 'MES':
            if self.periodo == 1:
                return 'mes'
            else:
                return 'meses'
        elif self.unidade_periodo == 'DIA':
            if self.periodo == 1:
                return 'dia'
            else:
                return 'dias'
        return ''
    
class JurosDebenture (models.Model):
    debenture = models.OneToOneField('Debenture', on_delete=models.CASCADE, primary_key=True)
    taxa = models.DecimalField(u'Taxa', max_digits=7, decimal_places=4)
    periodo = models.IntegerField(u'Período')
    unidade_periodo = models.CharField(u'Unidade do período', max_length=10)
    carencia = models.DateField(u'Carência', blank=True, null=True)
    data = models.DateField(u'Data')
    
    def descricao(self):
        if self.taxa > 0:
            self.taxa = str(self.taxa).replace('.', ',')
            if (self.periodo == 0 and self.unidade_periodo == '-'):
                return '%s%% ao ano, a partir de %s' % (self.taxa, self.carencia.strftime('%d/%m/%Y'))
            else:
                return '%s%% a cada %s %s, a partir de %s' % (self.taxa, self.periodo, self.descricao_unidade_periodo(), self.carencia.strftime('%d/%m/%Y'))
        else:
            return ''
    
    def descricao_unidade_periodo(self):
        if self.unidade_periodo == 'MES':
            if self.periodo == 1:
                return 'mes'
            else:
                return 'meses'
        elif self.unidade_periodo == 'DIA':
            if self.periodo == 1:
                return 'dia'
            else:
                return 'dias'
        return ''
    
class PremioDebenture (models.Model):
    debenture = models.OneToOneField('Debenture', on_delete=models.CASCADE, primary_key=True)
    taxa = models.DecimalField(u'Taxa', max_digits=7, decimal_places=4)
    periodo = models.IntegerField(u'Período')
    unidade_periodo = models.CharField(u'Unidade do período', max_length=10)
    carencia = models.DateField(u'Carência', blank=True, null=True)
    data = models.DateField(u'Data')
    
    def descricao(self):
        if self.taxa > 0:
            self.taxa = str(self.taxa).replace('.', ',')
            return '%s%% a cada %s %s, a partir de %s' % (self.taxa, self.periodo, self.descricao_unidade_periodo(), self.carencia.strftime('%d/%m/%Y'))
        else:
            return ''
    
    def descricao_unidade_periodo(self):
        if self.unidade_periodo == 'MES':
            if self.periodo == 1:
                return 'mes'
            else:
                return 'meses'
        return ''
        
class OperacaoDebenture (models.Model):
    investidor = models.ForeignKey('Investidor')
    debenture = models.ForeignKey('Debenture')
    preco_unitario = models.DecimalField(u'Preço unitário', max_digits=15, decimal_places=8)  
    quantidade = models.IntegerField(u'Quantidade') 
    data = models.DateField(u'Data', blank=True, null=True)
    taxa = models.DecimalField(u'Taxa', max_digits=11, decimal_places=2)
    tipo_operacao = models.CharField(u'Tipo de operação', max_length=1)
    
class HistoricoValorDebenture (models.Model):
    debenture = models.ForeignKey('Debenture')
    valor_nominal = models.DecimalField(u'Valor nominal', max_digits=15, decimal_places=6)
    juros = models.DecimalField(u'Juros', max_digits=15, decimal_places=6)
    premio = models.DecimalField(u'Prêmio', max_digits=15, decimal_places=6)
    data = models.DateField(u'Data')