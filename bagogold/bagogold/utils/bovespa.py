# -*- coding: utf-8 -*-
from urllib2 import urlopen
import re

def preencher_empresa_fii_nao_listado(ticker):
    """
    Preenche a empresa para um FII que nã está mais listado na Bovespa
    Parâmetros: Ticker do FII
    """
    url = 'http://bvmf.bmfbovespa.com.br/Fundos-Listados/FundosListadosDetalhe.aspx?Sigla=%s&tipoFundo=Imobiliario&aba=abaPrincipal&idioma=pt-br' % ticker[0:4]
    resposta = urlopen(url)
    string_retorno = resposta.read()
    if 'Sistema indisponivel' in string_retorno:
        raise ValueError(u'O sistema está indisponível')
    nome_empresa = re.findall('<span id="ctl00_contentPlaceHolderConteudo_lblNomeFundo" class="label">(.+?)</span>', string_retorno)
    print nome_empresa
    string_importante = string_retorno[string_retorno.find('Nome de Pregão'):string_retorno.find('Códigos de Negociação')]
    nome_pregao = re.sub('<span id="ctl00_contentPlaceHolderConteudo_ucFundoDetalhes_lblNomeFundo">FII GEN SHOP</span>', '\1', flags=re.DOTALL)
    print nome_pregao