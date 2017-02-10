# -*- coding: utf-8 -*-
from bagogold.pendencias.models.pendencias import \
    PendenciaVencimentoTesouroDireto

def buscar_pendencias_investidor(investidor):
    """
    Traz todas as pendências de um investidor
    Parâmetros: Investidor
    Retorno:    Lista com todas as pendências do investidor
    """
    lista_pendencias = list()
    lista_classes_pendencias = [PendenciaVencimentoTesouroDireto]
    for classe in lista_classes_pendencias:
        print dir(classe)
        lista_pendencias += list(classe.objects.filter(investidor=investidor))
    return lista_pendencias