# -*- coding: utf-8 -*-
from django import forms
from django.db import models
import datetime

class Administrador (models.Model):
    nome = models.CharField(u'Nome', max_length=100)
    cnpj = models.CharField(u'CNPJ', max_length=20)

class FundoInvestimento (models.Model):
    PRAZO_CURTO = 'C'
    PRAZO_LONGO = 'L'
    TIPOS_PRAZO = [(PRAZO_CURTO, 'Curto'),
                   (PRAZO_LONGO, 'Longo')
                   ]
    
    SITUACAO_FUNCIONAMENTO_NORMAL = 1
    SITUACAO_FUNCIONAMENTO_NORMAL_DESCRICAO = 'Em funcionamento normal'
    TIPOS_SITUACAO = [(SITUACAO_FUNCIONAMENTO_NORMAL, SITUACAO_FUNCIONAMENTO_NORMAL_DESCRICAO),
                      ]
    
    TIPOS_CLASSE = []
    
    nome = models.CharField(u'Nome', max_length=100)
    cnpj = models.CharField(u'CNPJ', max_length=20)
    administrador = models.ForeignKey('Administrador')
    data_inicio = models.DateField('Data de início')
    situacao = models.PositiveSmallIntegerField(u'Situação', choices=TIPOS_SITUACAO)
    """
    L = longo prazo, C = curto prazo; para fins de IR
    """
    tipo_prazo = models.CharField(u'Tipo de prazo', max_length=1, choices=TIPOS_PRAZO)
    classe = models.PositiveSmallIntegerField(u'Classe', choices=TIPOS_CLASSE)
    exclusivo_qualificados = models.BooleanField(u'Exclusivo para investidores qualificados?')
    
    
    def __unicode__(self):
        return self.nome
    
    def valor_no_dia(self, dia=datetime.date.today()):
        historico_fundo = HistoricoValorCotas.objects.filter(fundo_investimento=self).order_by('-data')
        ultima_operacao_fundo = OperacaoFundoInvestimento.objects.filter(fundo_investimento=self).order_by('-data')[0]
        if historico_fundo and historico_fundo[0].data > ultima_operacao_fundo.data:
            return historico_fundo[0].valor_cota
        else:
            return ultima_operacao_fundo.valor_cota()
    
class OperacaoFundoInvestimento (models.Model):
    quantidade = models.DecimalField(u'Quantidade de cotas', max_digits=11, decimal_places=2)
    valor = models.DecimalField(u'Valor da operação', max_digits=11, decimal_places=2)
    data = models.DateField(u'Data da operação')
    tipo_operacao = models.CharField(u'Tipo de operação', max_length=1)
    fundo_investimento = models.ForeignKey('FundoInvestimento')
    investidor = models.ForeignKey('Investidor')
    
    def __unicode__(self):
        return '(%s) R$%s de %s em %s' % (self.tipo_operacao, self.quantidade, self.fundo_investimento, self.data)
    
    def valor_cota(self):
        return self.valor/self.quantidade if self.quantidade > 0 else 0

class HistoricoValorCotas (models.Model):
    fundo_investimento = models.ForeignKey('FundoInvestimento')
    data = models.DateField(u'Data')
    valor_cota = models.DecimalField(u'Valor da cota', max_digits=11, decimal_places=2)

    def save(self, *args, **kw):
        try:
            historico = HistoricoValorCotas.objects.get(fundo_investimento=self.fundo_investimento, data=self.data)
        except HistoricoValorCotas.DoesNotExist:
            if self.valor_cota <= 0:
                raise forms.ValidationError('Valor da cota deve ser superior a zero')
            super(HistoricoValorCotas, self).save(*args, **kw)

