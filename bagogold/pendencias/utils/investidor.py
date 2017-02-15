# -*- coding: utf-8 -*-
from bagogold.bagogold.models.td import OperacaoTitulo
from bagogold.pendencias.models.pendencias import \
    PendenciaVencimentoTesouroDireto, Pendencia
from django.db.models.aggregates import Sum
from django.db.models.expressions import Case, When, F
from django.db.models.fields import DecimalField
import datetime

def buscar_pendencias_investidor(investidor):
    """
    Traz todas as pendências de um investidor
    Parâmetros: Investidor
    Retorno:    Lista com todas as pendências do investidor
    """
    lista_pendencias = list()
    for classe in Pendencia.__subclasses__():
        lista_pendencias += list(classe.objects.filter(investidor=investidor))
    return lista_pendencias

def verificar_pendencias_investidor(investidor):
    """
    Verifica todas as pendências que um investidor pode ter
    Parâmetros: Investidor
    """
    # Pendências de vencimento de Tesouro Direto
    qtd_titulos_vencidos = list(OperacaoTitulo.objects.filter(investidor=investidor, titulo__data_vencimento__lte=datetime.date.today()) \
        .values('titulo') \
        .annotate(qtd_soma=Sum(Case(When(tipo_operacao='C', then=F('quantidade')),
                            When(tipo_operacao='V', then=F('quantidade')*-1),
                            output_field=DecimalField()))))
    
    for titulo_qtd in qtd_titulos_vencidos:
        if titulo_qtd['qtd_soma'] > 0:
            PendenciaVencimentoTesouroDireto.verificar_pendencia(investidor, titulo_qtd['titulo'], titulo_qtd['qtd_soma'])
