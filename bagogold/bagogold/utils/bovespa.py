# -*- coding: utf-8 -*-
from StringIO import StringIO
from bagogold.bagogold.models.acoes import HistoricoAcao, Acao
from bagogold.bagogold.models.empresa import Empresa
from bagogold.bagogold.models.fii import FII, HistoricoFII
from decimal import Decimal
from django.db import transaction
from lxml import etree
from mechanize._form import ControlNotFoundError
from urllib2 import urlopen
import datetime
import mechanize
import re
import zipfile

def preencher_empresa_fii_nao_listado(ticker, num_tentativas=0):
    """
    Preenche a empresa para um FII que não está mais listado na Bovespa
    Parâmetros: Ticker do FII
    """
#     print ticker
    url = 'http://bvmf.bmfbovespa.com.br/Fundos-Listados/FundosListadosDetalhe.aspx?Sigla=%s&tipoFundo=Imobiliario&aba=abaPrincipal&idioma=pt-br' % ticker[0:4]
    resposta = urlopen(url)
    string_retorno = resposta.read()
    if 'Sistema indisponivel' in string_retorno:
        if (num_tentativas == 3):
            raise ValueError('O sistema está indisponível')
        preencher_empresa_fii_nao_listado(ticker, num_tentativas+1)
    nome_empresa = re.findall(r'<span id="ctl00_contentPlaceHolderConteudo_lblNomeFundo" class="label">(.+?)</span>', string_retorno)[0].strip('')
#     print nome_empresa
    string_importante = string_retorno[string_retorno.find('Nome de Pregão'):string_retorno.find('Códigos de Negociação')]
    nome_pregao = re.sub(r'.*?<span id="ctl00_contentPlaceHolderConteudo_ucFundoDetalhes_lblNomeFundo">(.+?)</span>.*', r'\1', string_importante, flags=re.DOTALL)
#     print nome_pregao
    empresa = Empresa(nome=nome_empresa, nome_pregao=nome_pregao, codigo_cvm=ticker[0:4])
    empresa.save()
    
def buscar_historico_recente_bovespa(data):
    """
    Busca o relatório de negociação do dia atual
    Retorno: Nome do arquivo com o histórico gerado
    """
    url = 'http://www.bmf.com.br/arquivos1/lum-arquivos_ipn.asp?idioma=pt-BR&status=ativo'
    # Usar mechanize para simular clique do usuario no javascript
    br = mechanize.Browser()
    br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    response = br.open(url)
    
    response.read()

    try:
        br.select_form(nr=0)
        br.form.set_all_readonly(False)
        text_control = [control for control in br.form.controls if control.type == 'text'][27]
        text_control.disabled = False
        text_control.value = data.strftime('%d/%m/%Y')
        br.find_control("chkArquivoDownload_ativo").disabled = False
        br.find_control("chkArquivoDownload_ativo").items[27].selected = True
        response = br.submit()
        
#         fileobj = open("teste.ex_","w+")
#         fileobj.write(response.read())
#         fileobj.close()
        
        arquivo_zipado = StringIO(response.read())
        unzipped = zipfile.ZipFile(arquivo_zipado)
            
        # Ler arquivo mais recente
        ult_arq_zip = max(unzipped.namelist())
        file(ult_arq_zip,'wb').write(unzipped.read(ult_arq_zip))
        
        return ult_arq_zip
            
    except ControlNotFoundError:
        raise ValueError(u'Não encontrou os controles')

def processar_historico_recente_bovespa(nome_arquivo_hist):
    """
    Processa o arquivo com o histórico recente da bovespa
    Parâmetros: Nome do arquivo
    """
    try:
        tree = etree.parse(open(nome_arquivo_hist))
        with transaction.atomic():
            namespace = '{urn:bvmf.217.01.xsd}'
            if len(tree.findall('.//%sPricRpt' % namespace)) == 0:
                raise ValueError('Não encontrou nenhum resultado')
            # Lê o arquivo procurando nós PricRpt (1 para cada ação/fii)
            for element in tree.findall('.//%sPricRpt' % namespace):
                if element.find('.//%sTckrSymb' % namespace) is not None and element.find('.//%sLastPric' % namespace) is not None \
                    and element.find('.//%sDt' % namespace) is not None:
                    ticker = element.find('.//%sTckrSymb' % namespace).text
                    preco = Decimal(element.find('.//%sLastPric' % namespace).text)
                    data = element.find('.//%sDt' % namespace).text
#                     print ticker, preco
                    if Acao.objects.filter(ticker=ticker).exists() and not HistoricoAcao.objects.filter(data=data, acao=Acao.objects.get(ticker=ticker), preco_unitario=preco, oficial_bovespa=True).exists():
                        hist = HistoricoAcao.objects.create(data=data, acao=Acao.objects.get(ticker=ticker), preco_unitario=preco, oficial_bovespa=True)
#                         print ticker, hist.data
                    elif FII.objects.filter(ticker=ticker).exists() and not HistoricoFII.objects.filter(data=data, fii=FII.objects.get(ticker=ticker), preco_unitario=preco, oficial_bovespa=True).exists():
                        hist = HistoricoFII.objects.create(data=data, fii=FII.objects.get(ticker=ticker), preco_unitario=preco, oficial_bovespa=True)
#                         print ticker, hist.data
    except:
        raise