# -*- coding: utf-8 -*-
from bagogold.bagogold.models.empresa import Empresa
from urllib2 import urlopen
import re

def preencher_empresa_fii_nao_listado(ticker, num_tentativas=0):
    """
    Preenche a empresa para um FII que não está mais listado na Bovespa
    Parâmetros: Ticker do FII
    """
    print ticker
    url = 'http://bvmf.bmfbovespa.com.br/Fundos-Listados/FundosListadosDetalhe.aspx?Sigla=%s&tipoFundo=Imobiliario&aba=abaPrincipal&idioma=pt-br' % ticker[0:4]
    resposta = urlopen(url)
    string_retorno = resposta.read()
    if 'Sistema indisponivel' in string_retorno:
        if (num_tentativas == 3):
            raise ValueError('O sistema está indisponível')
        preencher_empresa_fii_nao_listado(ticker, num_tentativas+1)
    nome_empresa = re.findall(r'<span id="ctl00_contentPlaceHolderConteudo_lblNomeFundo" class="label">(.+?)</span>', string_retorno)[0].strip('')
    print nome_empresa
    string_importante = string_retorno[string_retorno.find('Nome de Pregão'):string_retorno.find('Códigos de Negociação')]
    nome_pregao = re.sub(r'.*?<span id="ctl00_contentPlaceHolderConteudo_ucFundoDetalhes_lblNomeFundo">(.+?)</span>.*', r'\1', string_importante, flags=re.DOTALL)
    print nome_pregao
    empresa = Empresa(nome=nome_empresa, nome_pregao=nome_pregao, codigo_cvm=ticker[0:4])
    empresa.save()