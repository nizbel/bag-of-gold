# -*- coding: utf-8 -*-
import datetime

from django.db import models
from django.urls.base import reverse


class Titulo (models.Model):
    TIPO_OFICIAL_LETRA_TESOURO = 'LTN'
    TIPO_OFICIAL_SELIC = 'LFT'
    TIPO_OFICIAL_IPCA_COM_JUROS = 'NTN-B'
    TIPO_OFICIAL_IPCA = 'NTN-B Principal'
    TIPO_OFICIAL_PREFIXADO_COM_JUROS = 'NTN-F'
    TIPO_OFICIAL_IGPM = 'NTN-C'
    
    TIPO_LETRA_TESOURO = ['LTN', 'Tesouro Prefixado']
    TIPO_SELIC = ['LFT', 'Tesouro Selic']
    TIPO_IPCA_COM_JUROS = ['NTN-B', 'NTNB', 'Tesouro IPCA+ com Juros Semestrais']
    TIPO_IPCA = ['NTN-B Principal', 'NTNBP', 'NTN-B Princ', 'NTNB Princ', 'Tesouro IPCA+']
    TIPO_PREFIXADO_COM_JUROS = ['NTN-F', 'NTNF', 'Tesouro Prefixado com Juros Semestrais']
    TIPO_IGPM = ['NTN-C','NTNC', 'Tesouro IGPM+ com Juros Semestrais']
    
    VINCULO_TIPOS_OFICIAL = {TIPO_OFICIAL_LETRA_TESOURO: TIPO_LETRA_TESOURO, TIPO_OFICIAL_SELIC: TIPO_SELIC, TIPO_OFICIAL_IPCA_COM_JUROS: TIPO_IPCA_COM_JUROS, 
                             TIPO_OFICIAL_IPCA: TIPO_IPCA, TIPO_OFICIAL_PREFIXADO_COM_JUROS: TIPO_PREFIXADO_COM_JUROS, TIPO_OFICIAL_IGPM: TIPO_IGPM}
    
    tipo = models.CharField(u'Tipo do título', max_length=20, unique_for_date='data_vencimento') 
    data_vencimento = models.DateField(u'Data de vencimento')
    data_inicio = models.DateField(u'Data de início')
    
    class Meta:
        unique_together=('tipo', 'data_vencimento')
        
    def nome(self):
        if self.tipo in self.TIPO_LETRA_TESOURO:
            return u'Tesouro Prefixado %s' % (self.data_vencimento.year)
        elif self.tipo in self.TIPO_SELIC:
            return u'Tesouro Selic %s' % (self.data_vencimento.year)
        elif self.tipo in self.TIPO_IPCA_COM_JUROS:
            return u'Tesouro IPCA+ com Juros Semestrais %s' % (self.data_vencimento.year)
        elif self.tipo in self.TIPO_IPCA:
            return u'Tesouro IPCA+ %s' % (self.data_vencimento.year)
        elif self.tipo in self.TIPO_PREFIXADO_COM_JUROS:
            return u'Tesouro Prefixado com Juros Semestrais %s' % (self.data_vencimento.year)
        elif self.tipo in self.TIPO_IGPM:
            return u'Tesouro IGP-M com Juros Semestrais %s' % (self.data_vencimento.year)
        # Se não encontrou
        return u'Título não encontrado'
    
    def __unicode__(self):
        return u'%s (%s)' % (self.nome(), self.tipo)
    
    @staticmethod
    def buscar_vinculo_oficial(tipo):
        for tipo_oficial, possiveis_tipos in Titulo.VINCULO_TIPOS_OFICIAL.items():
            if tipo in possiveis_tipos:
                return tipo_oficial
        raise ValueError(u'Tipo %s é inválido' % (tipo))
    
    def indexador(self):
        if self.tipo in self.TIPO_LETRA_TESOURO + self.TIPO_PREFIXADO_COM_JUROS:
            return u'Prefixado'
        elif self.tipo in self.TIPO_SELIC:
            return u'Selic'
        elif self.tipo in self.TIPO_IPCA_COM_JUROS + self.TIPO_IPCA:
            return u'IPCA'
        elif self.tipo in self.TIPO_IGPM:
            return u'IGP-M'
        # Se não encontrou
        return u'Indefinido'
    
    def titulo_vencido(self):
        if datetime.date.today() >= self.data_vencimento:
            return True
        return False
        
    def valor_vencimento(self, data=None):
        from bagogold.bagogold.utils.taxas_indexacao import calcular_valor_acumulado_ipca, \
            calcular_valor_acumulado_selic
        
        if data == None:
            data = datetime.date.today()
        
        if self.tipo in self.TIPO_LETRA_TESOURO:
            return 1000
        elif self.tipo in self.TIPO_SELIC:
            return (1 + calcular_valor_acumulado_selic(datetime.date(2000, 7, 1), data_final=data)) * 1000
        elif self.tipo in self.TIPO_IPCA_COM_JUROS:
            return (1 + calcular_valor_acumulado_ipca(datetime.date(2000, 7, 16), data_final=data)) * 1000
        elif self.tipo in self.TIPO_IPCA:
            return (1 + calcular_valor_acumulado_ipca(datetime.date(2000, 7, 16), data_final=data)) * 1000
        elif self.tipo in self.TIPO_PREFIXADO_COM_JUROS:
            return 1000
        elif self.tipo in self.TIPO_IGPM:
            # TODO adicionar calculo, data base é 15/07/2000
            return 1000
        # Se não encontrou
        return 0
    
    @staticmethod
    def codificar_slug(tipo):
        if tipo in Titulo.TIPO_LETRA_TESOURO:
            return 'LTN'
        elif tipo in Titulo.TIPO_SELIC:
            return 'LFT'
        elif tipo in Titulo.TIPO_IPCA_COM_JUROS:
            return 'NTNB'
        elif tipo in Titulo.TIPO_IPCA:
            return 'NTNBP'
        elif tipo in Titulo.TIPO_PREFIXADO_COM_JUROS:
            return 'NTNF'
        elif tipo in Titulo.TIPO_IGPM:
            return 'NTNC'
    
    @staticmethod
    def decodificar_slug(slug):
        if slug == 'LTN':
            return Titulo.TIPO_OFICIAL_LETRA_TESOURO
        elif slug == 'LFT':
            return Titulo.TIPO_OFICIAL_SELIC
        elif slug == 'NTNB':
            return Titulo.TIPO_OFICIAL_IPCA_COM_JUROS
        elif slug == 'NTNBP':
            return Titulo.TIPO_OFICIAL_IPCA
        elif slug == 'NTNF':
            return Titulo.TIPO_OFICIAL_PREFIXADO_COM_JUROS
        elif slug == 'NTNC':
            return Titulo.TIPO_OFICIAL_IGPM
    
class OperacaoTitulo (models.Model):
    preco_unitario = models.DecimalField(u'Preço unitário', max_digits=11, decimal_places=2)  
    quantidade = models.DecimalField(u'Quantidade', max_digits=7, decimal_places=2) 
    data = models.DateField(u'Data', blank=True, null=True)
    taxa_bvmf = models.DecimalField(u'Taxa BVMF', max_digits=11, decimal_places=2)
    taxa_custodia = models.DecimalField(u'Taxa do agente de custódia', max_digits=11, decimal_places=2)
    tipo_operacao = models.CharField(u'Tipo de operação', max_length=1)
    titulo = models.ForeignKey('Titulo')
    consolidada = models.NullBooleanField(u'Consolidada?', blank=True, null=True)
    investidor = models.ForeignKey('bagogold.Investidor')
    
    def __unicode__(self):
        return '(' + self.tipo_operacao + ') ' +str(self.quantidade) + ' ' + self.titulo.tipo + ' a R$' + str(self.preco_unitario)
    
    def data_vencimento(self):
        return self.titulo.data_vencimento
    
    @property
    def link(self):
        return reverse('tesouro_direto:editar_operacao_td', kwargs={'id_operacao': self.id})
    
class HistoricoTitulo (models.Model):
    titulo = models.ForeignKey('Titulo', unique_for_date='data')
    data = models.DateField(u'Data')
    taxa_compra = models.DecimalField(u'Taxa de compra', max_digits=5, decimal_places=2)
    taxa_venda = models.DecimalField(u'Taxa de venda', max_digits=5, decimal_places=2)
    preco_compra = models.DecimalField(u'Preço de compra', max_digits=11, decimal_places=2)
    preco_venda = models.DecimalField(u'Preço de venda', max_digits=11, decimal_places=2)
    
    class Meta:
        unique_together=('titulo', 'data')
    
    def __unicode__(self):
        return str(self.titulo) + ' em ' + str(self.data) + ': R$' + str(self.preco_compra) + '(' + str(self.taxa_compra) + ')' + \
            '/R$' + str(self.preco_venda) + '(' + str(self.taxa_venda) + ')'
    
class ValorDiarioTitulo (models.Model):
    titulo = models.ForeignKey('Titulo')
    data_hora = models.DateTimeField(u'Horário')
    taxa_compra = models.DecimalField(u'Taxa de compra', max_digits=5, decimal_places=2)
    taxa_venda = models.DecimalField(u'Taxa de venda', max_digits=5, decimal_places=2)
    preco_compra = models.DecimalField(u'Preço de compra', max_digits=11, decimal_places=2)
    preco_venda = models.DecimalField(u'Preço de venda', max_digits=11, decimal_places=2)
    
    class Meta:
        unique_together=('titulo', 'data_hora')
        
    def __unicode__(self):
        return u'%s, C/V: R$ %s (%s%%) / R$ %s (%s%%)' % (self.titulo, self.preco_compra, self.taxa_compra, self.preco_venda, self.taxa_venda)
        