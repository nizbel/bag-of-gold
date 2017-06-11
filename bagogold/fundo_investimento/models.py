# -*- coding: utf-8 -*-
from django import forms
from django.db import models
import datetime

class Administrador (models.Model):
    nome = models.CharField(u'Nome', max_length=100)
    cnpj = models.CharField(u'CNPJ', max_length=20)
    
    class Meta:
        unique_together=('cnpj',)
        
    def __unicode__(self):
        return self.nome

class FundoInvestimento (models.Model):
    PRAZO_CURTO = 'C'
    PRAZO_LONGO = 'L'
    TIPOS_PRAZO = [(PRAZO_CURTO, 'Curto'),
                   (PRAZO_LONGO, 'Longo'),
                   ]
    
    SITUACAO_FUNCIONAMENTO_NORMAL = 1
    SITUACAO_FUNCIONAMENTO_NORMAL_DESCRICAO = u'Em funcionamento normal'
    SITUACAO_PRE_OPERACIONAL = 2
    SITUACAO_PRE_OPERACIONAL_DESCRICAO = u'Fase pré-operacional'
    SITUACAO_TERMINADO = 3
    SITUACAO_TERMINADO_DESCRICAO = u'Terminado'
    SITUACAO_ESPECIAL = 4
    SITUACAO_ESPECIAL_DESCRICAO = u'Em situação especial'
    TIPOS_SITUACAO = [(SITUACAO_FUNCIONAMENTO_NORMAL, SITUACAO_FUNCIONAMENTO_NORMAL_DESCRICAO),
                      (SITUACAO_PRE_OPERACIONAL, SITUACAO_PRE_OPERACIONAL_DESCRICAO),
                      (SITUACAO_TERMINADO, SITUACAO_TERMINADO_DESCRICAO),
                      (SITUACAO_ESPECIAL, SITUACAO_ESPECIAL_DESCRICAO),
                      ]
    
    CLASSE_FUNDO_INDEFINIDA = 0
    CLASSE_FUNDO_INDEFINIDA_DESCRICAO = u'Indefinida'
    CLASSE_FUNDO_ACOES = 1
    CLASSE_FUNDO_ACOES_DESCRICAO = u'Fundo de Ações'
    CLASSE_FUNDO_RENDA_FIXA = 2
    CLASSE_FUNDO_RENDA_FIXA_DESCRICAO = u'Fundo de Renda Fixa'
    CLASSE_FUNDO_MULTIMERCADO = 3
    CLASSE_FUNDO_MULTIMERCADO_DESCRICAO = u'Fundo Multimercado'
    CLASSE_FUNDO_REFERENCIADO = 4
    CLASSE_FUNDO_REFERENCIADO_DESCRICAO = u'Fundo Referenciado'
    CLASSE_FUNDO_DIVIDA_EXTERNA = 5
    CLASSE_FUNDO_DIVIDA_EXTERNA_DESCRICAO = u'Fundo da Dívida Externa'
    CLASSE_FUNDO_CAMBIAL = 6
    CLASSE_FUNDO_CAMBIAL_DESCRICAO = u'Fundo Cambial'
    CLASSE_FUNDO_CURTO_PRAZO = 7
    CLASSE_FUNDO_CURTO_PRAZO_DESCRICAO = u'Fundo de Curto Prazo'
    TIPOS_CLASSE = [(CLASSE_FUNDO_INDEFINIDA, CLASSE_FUNDO_INDEFINIDA_DESCRICAO),
                    (CLASSE_FUNDO_ACOES, CLASSE_FUNDO_ACOES_DESCRICAO),
                    (CLASSE_FUNDO_RENDA_FIXA, CLASSE_FUNDO_RENDA_FIXA_DESCRICAO),
                    (CLASSE_FUNDO_MULTIMERCADO, CLASSE_FUNDO_MULTIMERCADO_DESCRICAO),
                    (CLASSE_FUNDO_REFERENCIADO, CLASSE_FUNDO_REFERENCIADO_DESCRICAO),
                    (CLASSE_FUNDO_DIVIDA_EXTERNA, CLASSE_FUNDO_DIVIDA_EXTERNA_DESCRICAO),
                    (CLASSE_FUNDO_CAMBIAL, CLASSE_FUNDO_CAMBIAL_DESCRICAO),
                    (CLASSE_FUNDO_CURTO_PRAZO, CLASSE_FUNDO_CURTO_PRAZO_DESCRICAO),
                    ]
    
    nome = models.CharField(u'Nome', max_length=100)
    cnpj = models.CharField(u'CNPJ', max_length=20)
    administrador = models.ForeignKey('Administrador')
    data_constituicao = models.DateField('Data de constituição')
    situacao = models.PositiveSmallIntegerField(u'Situação', choices=TIPOS_SITUACAO)
    """
    L = longo prazo, C = curto prazo; para fins de IR
    """
    tipo_prazo = models.CharField(u'Tipo de prazo', max_length=1, choices=TIPOS_PRAZO)
    classe = models.PositiveSmallIntegerField(u'Classe', choices=TIPOS_CLASSE)
    exclusivo_qualificados = models.BooleanField(u'Exclusivo para investidores qualificados?')
    """
    Última data de documento de cadastro que conteve registro do fundo
    """
    ultimo_registro = models.DateField(u'Último registro')
    
    class Meta:
        unique_together=('cnpj',)
    
    def __unicode__(self):
        return self.nome
    
    def valor_no_dia(self, dia=datetime.date.today()):
        historico_fundo = HistoricoValorCotas.objects.filter(fundo_investimento=self).order_by('-data')
        ultima_operacao_fundo = OperacaoFundoInvestimento.objects.filter(fundo_investimento=self).order_by('-data')[0]
        if historico_fundo and historico_fundo[0].data > ultima_operacao_fundo.data:
            return historico_fundo[0].valor_cota
        else:
            return ultima_operacao_fundo.valor_cota()
        
    def descricao_classe(self):
        for codigo, descricao in FundoInvestimento.TIPOS_CLASSE:
            if codigo == self.classe:
                return descricao 
            
    def descricao_situacao(self):
        for codigo, descricao in FundoInvestimento.TIPOS_SITUACAO:
            if codigo == self.situacao:
                return descricao 
        
    @staticmethod
    def buscar_tipo_classe(descricao_classe):
        # Se nulo, retornar classe indefinida
        if descricao_classe == None:
            return FundoInvestimento.CLASSE_FUNDO_INDEFINIDA
        for tipo in FundoInvestimento.TIPOS_CLASSE:
            if descricao_classe.strip().lower() == tipo[1].strip().lower():
                return tipo[0]
        raise ValueError(u'Classe não encontrada: %s' % (descricao_classe))
    
    @staticmethod
    def buscar_tipo_situacao(descricao_situacao):
        # Se nulo, retornar situação de funcionamento normal
        if descricao_situacao == None:
            return FundoInvestimento.SITUACAO_FUNCIONAMENTO_NORMAL
        for tipo in FundoInvestimento.TIPOS_SITUACAO:
#             print descricao_situacao.lower(), tipo[1].lower(), [i for i in xrange(len(descricao_situacao.lower())) if descricao_situacao.lower()[i] != tipo[1].lower()[i]]
            if descricao_situacao.strip().lower() == tipo[1].strip().lower():
                return tipo[0]
        raise ValueError(u'Situação não encontrada: %s' % (descricao_situacao))
    
class OperacaoFundoInvestimento (models.Model):
    quantidade = models.DecimalField(u'Quantidade de cotas', max_digits=11, decimal_places=2)
    valor = models.DecimalField(u'Valor total da operação', max_digits=11, decimal_places=2)
    data = models.DateField(u'Data da operação')
    tipo_operacao = models.CharField(u'Tipo de operação', max_length=1)
    fundo_investimento = models.ForeignKey('FundoInvestimento')
    investidor = models.ForeignKey('bagogold.Investidor', related_name='fundo_investimento')
    
    def __unicode__(self):
        return '(%s) R$%s de %s em %s' % (self.tipo_operacao, self.quantidade, self.fundo_investimento, self.data)
    
    def valor_cota(self):
        return self.valor/self.quantidade if self.quantidade > 0 else 0

class HistoricoValorCotas (models.Model):
    fundo_investimento = models.ForeignKey('FundoInvestimento')
    data = models.DateField(u'Data')
    valor_cota = models.DecimalField(u'Valor da cota', max_digits=24, decimal_places=15)

    class Meta:
        unique_together=('fundo_investimento', 'data')
    
# Guarda documentos de cadastro da CVM lidos        
class DocumentoCadastro (models.Model):
    data_referencia = models.DateField(u'Data de referência')
    data_pedido_cvm = models.DateField(u'Data de pedido à CVM')
    leitura_realizada = models.BooleanField(u'Leitura realizada', default=False)
    
    class Meta:
        unique_together=('data_referencia',)

class LinkDocumentoCadastro (models.Model):
    url = models.URLField(u'URL do documento de cadastro')
    documento = models.OneToOneField('DocumentoCadastro')
    
