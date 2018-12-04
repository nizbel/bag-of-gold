# -*- coding: utf-8 -*-
from StringIO import StringIO
import datetime
from decimal import Decimal
import re
from urllib2 import urlopen
import zipfile

import boto3
from django.db import transaction
from lxml import etree
import mechanize
from mechanize._form import ControlNotFoundError

from bagogold.bagogold.models.acoes import HistoricoAcao, Acao
from bagogold.bagogold.models.empresa import Empresa
from bagogold.fii.models import FII, HistoricoFII
from bagogold.settings import CAMINHO_HISTORICO_RECENTE_ACOES_FIIS
from conf.settings_local import AWS_STORAGE_BUCKET_NAME


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
        text_control = [control for control in br.form.controls if control.type == 'text'][25]
        text_control.disabled = False
        text_control.value = data.strftime('%d/%m/%Y')
        br.find_control("chkArquivoDownload_ativo").disabled = False
        br.find_control("chkArquivoDownload_ativo").items[25].selected = True
        response = br.submit()
        
#         fileobj = open("teste.ex_","w+")
#         fileobj.write(response.read())
#         fileobj.close()
        
        arquivo_zipado = StringIO(response.read())
        unzipped = zipfile.ZipFile(arquivo_zipado)
            
        # Ler arquivo mais recente
        ult_arq_zip = max(unzipped.namelist())
        caminho_arquivo = CAMINHO_HISTORICO_RECENTE_ACOES_FIIS + ult_arq_zip
        boto3.client('s3').put_object(Body=unzipped.read(ult_arq_zip), Bucket=AWS_STORAGE_BUCKET_NAME, Key=caminho_arquivo)
#         open(caminho_arquivo,'wb').write(unzipped.read(ult_arq_zip))
        
#         print caminho_arquivo
        return caminho_arquivo
            
    except ControlNotFoundError:
        raise ValueError(u'Não encontrou os controles')

def processar_historico_recente_bovespa(arquivo):
    """
    Processa o arquivo com o histórico recente da bovespa
    
    Parâmetros: Arquivo a ser analisado
    """
    try:
        dados_arquivo = arquivo['Body']
        tree = etree.parse(dados_arquivo)
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
    
def ler_serie_historica_anual_bovespa(nome_arquivo):
    """
    Lê série histórica anual de documento da Bovespa
    
    Parâmetros: Nome do arquivo
    """
    # Carregar FIIs disponíveis
    fiis = FII.objects.all()
    acoes = Acao.objects.all()
    fiis_lista = fiis.values_list('ticker', flat=True)
    acoes_lista = acoes.values_list('ticker', flat=True)
    with open(nome_arquivo) as f:
        content = f.readlines()
        for line in content[1:len(content)-1]:
#             if line[2:10] == '20160215':
            data = datetime.date(int(line[2:6]), int(line[6:8]), int(line[8:10]))
            valor = Decimal(line[108:119] + '.' + line[119:121])
            ticker = line[12:24].strip()
            if ticker in fiis_lista:
                _, criado = HistoricoFII.objects.update_or_create(fii=fiis.get(ticker=ticker), data=data, defaults={'preco_unitario':valor, 'oficial_bovespa': True})
                if criado:
                    print ticker, 'em', data, 'criado'
            elif line[39:41] == 'ON' or (line[39:41] == 'PN'):
                if len(ticker) == 5 and int(ticker[4]) in [3,4,5,6,7,8]:
#                     print line[12:24], line[39:49]
                    if ticker in acoes_lista:
                        _, criado = HistoricoAcao.objects.update_or_create(acao=acoes.get(ticker=ticker), data=data, defaults={'preco_unitario':valor, 'oficial_bovespa': True})
                        if criado:
                            print ticker, 'em', data, 'criado (Histórico)'
                    else:
                        empresa_existe = False
                        for acao_listada in acoes_lista:
                            if ticker[0:4] in acao_listada:
#                                 print 'Inserido'
                                empresa_existe = True
                                empresa = Acao.objects.get(ticker=acao_listada).empresa
                                break
                        if not empresa_existe:
                            empresa = Empresa(nome=line[27:39].strip(), nome_pregao=line[27:39].strip())
                            empresa.save()
                        acao = Acao(ticker=ticker, empresa=empresa, tipo=verificar_tipo_acao(ticker))
                        acao.save()
                        _, criado = HistoricoAcao.objects.update_or_create(acao=acao, data=data, defaults={'preco_unitario':valor, 'oficial_bovespa': True})
                        print ticker, 'em', data, 'criado (TICKER)'
                        acoes = Acao.objects.all()
                        acoes_lista = acoes.values_list('ticker', flat=True)
            elif line[39:42] == 'UNT':
                if len(ticker) == 6 and ticker[4:6] == '11':
                    if ticker in acoes_lista:
                        _, criado = HistoricoAcao.objects.update_or_create(acao=acoes.get(ticker=ticker), data=data, defaults={'preco_unitario':valor, 'oficial_bovespa': True})
                        if criado:
                            print ticker, 'em', data, 'criado (Histórico)'
                    else:
                        empresa_existe = False
                        for acao_listada in acoes_lista:
                            if ticker[0:4] in acao_listada:
#                                 print 'Inserido'
                                empresa_existe = True
                                empresa = Acao.objects.get(ticker=acao_listada).empresa
                                break
                        if not empresa_existe:
                            empresa = Empresa(nome=line[27:39].strip(), nome_pregao=line[27:39].strip())
                            empresa.save()
                        acao = Acao(ticker=ticker, empresa=empresa, tipo=verificar_tipo_acao(ticker))
                        acao.save()
                        _, criado = HistoricoAcao.objects.update_or_create(acao=acao, data=data, defaults={'preco_unitario':valor, 'oficial_bovespa': True})
                        print ticker, 'em', data, 'criado (TICKER)'
                        acoes = Acao.objects.all()
                        acoes_lista = acoes.values_list('ticker', flat=True)