# -*- coding: utf-8 -*-
from bagogold import settings
from bagogold.bagogold.models.empresa import Empresa
from bagogold.bagogold.models.fii import FII, ProventoFII
from bagogold.bagogold.models.gerador_proventos import DocumentoProventoBovespa, \
    PendenciaDocumentoProvento, ProventoFIIDocumento, \
    ProventoFIIDescritoDocumentoBovespa
from bagogold.bagogold.utils.gerador_proventos import \
    ler_provento_estruturado_fii
from django.core.mail import mail_admins
from django.core.management.base import BaseCommand
from mechanize._form import ControlNotFoundError
from threading import Thread
from urllib2 import Request, urlopen, HTTPError, URLError
import datetime
import mechanize
import re
import time

# A thread 'Principal' indica se ainda está rodando a thread principal
threads_rodando = {'Principal': 1}
documentos_para_download = list()
informacoes_rendimentos = list()

class CriarDocumentoThread(Thread):
    def run(self):
        try:
            while len(threads_rodando) > 0 or len(documentos_para_download) > 0 or len(informacoes_rendimentos) > 0:
                while len(documentos_para_download) > 0:
                    documento = documentos_para_download.pop(0)
                    
                    # Baixar e salvar documento
                    documento.baixar_e_salvar_documento()
                
                time.sleep(5)
        except Exception as e:
                template = "An exception of type {0} occured. Arguments:\n{1!r}"
                message = template.format(type(e).__name__, e.args)
                if settings.ENV == 'PROD':
                    mail_admins(u'Erro na thread de criar documento de fiis', message.decode('utf-8'))
                elif settings.ENV == 'DEV':
                    print message
                
class GeraInfoDocumentoProtocoloThread(Thread):
    def run(self):
        try:
#             prot = list()
            while len(threads_rodando) > 0 or len(informacoes_rendimentos) > 0:
                while len(informacoes_rendimentos) > 0:
                    info = informacoes_rendimentos.pop(0)
                    ticker = info['ticker']
                    url = info['url']
                    data_referencia = info['data_ref']
                    tipo_documento = info['tipo']
                    protocolo = info['protocolo']
                    
                    # Apenas adiciona caso seja dos tipos válidos, decodificando de utf-8
                    if not DocumentoProventoBovespa.objects.filter(empresa__codigo_cvm=ticker[0:4], protocolo=protocolo).exists() \
                        and tipo_documento.decode('utf-8') in DocumentoProventoBovespa.TIPOS_DOCUMENTO_VALIDOS:
                        documento = DocumentoProventoBovespa()
                        documento.empresa = Empresa.objects.get(codigo_cvm=ticker[0:4])
                        documento.tipo_documento = tipo_documento
                        documento.url = url
                        documento.tipo = 'F'
                        documento.protocolo = protocolo
                        documento.data_referencia = datetime.datetime.strptime(data_referencia, '%d/%m/%Y')
#                         print documento
                        documentos_para_download.append(documento)
                
                time.sleep(10)
#             print list(reversed(sorted(prot, key=lambda tup: tup[0])))
        except Exception as e:
                template = "An exception of type {0} occured. Arguments:\n{1!r}"
                message = template.format(type(e).__name__, e.args)
                if settings.ENV == 'PROD':
                    mail_admins(u'Erro na thread de gerar infos do documento de fiis', message.decode('utf-8'))
                elif settings.ENV == 'DEV':
                    print message
                
class BuscaRendimentosFIIThread(Thread):
    def __init__(self, ticker, antigos, ano_inicial):
        self.ticker = ticker 
        self.antigos = antigos 
        self.ano_inicial = ano_inicial 
        super(BuscaRendimentosFIIThread, self).__init__()

    def run(self):
        try:
            if self.antigos:
                buscar_rendimentos_fii_antigos(self.ticker, 0)
            if self.ano_inicial != 0:
                buscar_rendimentos_fii(self.ticker, self.ano_inicial, 0)
        except Exception as e:
#             template = "An exception of type {0} occured. Arguments:\n{1!r}"
#             message = template.format(type(e).__name__, e.args)
            pass
        # Tenta remover seu código da listagem de threads até conseguir
        while self.ticker in threads_rodando:
            del threads_rodando[self.ticker]

class Command(BaseCommand):
    help = 'Busca rendimentos de FII na Bovespa'
    
    def add_arguments(self, parser):
        parser.add_argument('--ano_inicial', default=datetime.date.today().year)
        parser.add_argument('--todos', action='store_true')
        parser.add_argument('--antigos', action='store_true')

    def handle(self, *args, **options):
#         inicio = datetime.datetime.now()
        # Checa primeiro se é para buscar todos os rendimentos
        if options['todos']:
            antigos = True
            ano_inicial = 2016
        elif options['antigos']:
            antigos = True
            ano_inicial = 0
        else:
            # Ano inicial não pode ser abaixo de 2016
            if options['ano_inicial'] < 2016:
                raise ValueError('Ano inicial tem de ser no mínimo 2016')
            ano_inicial = options['ano_inicial']
            antigos = False
            
        # Prepara thread de criação de documentos no sistema
        for _ in range(6):
            thread_criar_documento = CriarDocumentoThread()
            thread_criar_documento.start()
            
        # Prepara thread de geração de info para documento
        thread_gerar_info = GeraInfoDocumentoProtocoloThread()
        thread_gerar_info.start()
            
        # Quantas threads correrão por vez
        qtd_threads = 8
#         fiis = Empresa.objects.filter(codigo_cvm__in=[fii.ticker[:4] for fii in FII.objects.filter(ticker='BRCR11')]).values_list('codigo_cvm', flat=True)
        fiis = Empresa.objects.filter(codigo_cvm__in=[fii.ticker[:4] for fii in FII.objects.all()]).values_list('codigo_cvm', flat=True)
        contador = 0
        try:
            while contador < len(fiis):
                fii = fiis[contador]
                t = BuscaRendimentosFIIThread(fii, antigos, ano_inicial)
                threads_rodando[fii] = 1
                t.start()
                contador += 1
                while (len(threads_rodando) > qtd_threads):
#                     print 'Documentos para download:', len(documentos_para_download), '... Threads:', len(threads_rodando), '... Infos:', len(informacoes_rendimentos), contador
                    time.sleep(3)
            while (len(threads_rodando) > 1 or len(documentos_para_download) > 0 or len(informacoes_rendimentos) > 0):
#                 print 'Documentos para download:', len(documentos_para_download), '... Threads:', len(threads_rodando), '... Infos:', len(informacoes_rendimentos), contador
                time.sleep(3)
            while 'Principal' in threads_rodando.keys():
                del threads_rodando['Principal']
                
            # Após buscar, tenta ler os proventos com documento estruturado
            for pendencia in PendenciaDocumentoProvento.objects.filter(documento__tipo_documento=DocumentoProventoBovespa.TIPO_DOCUMENTO_AVISO_COTISTAS_ESTRUTURADO,
                                                                   documento__tipo='F').order_by('documento__protocolo'):
                try:
                    ler_provento_estruturado_fii(pendencia.documento)
                except:
                    pass
        except KeyboardInterrupt:
#             print 'Documentos para download:', len(documentos_para_download), '... Threads:', len(threads_rodando), '... Infos:', len(informacoes_rendimentos), contador
            while 'Principal' in threads_rodando.keys():
                del threads_rodando['Principal']
                time.sleep(3)
#         print datetime.datetime.now() - inicio

def buscar_rendimentos_fii_antigos(ticker, num_tentativas):
    """
    Busca distribuições de rendimentos de FII no formato antigo no site da Bovespa
    """
    fii_url = 'http://bvmf.bmfbovespa.com.br/Fundos-Listados/FundosListadosDetalhe.aspx?Sigla=%s&tipoFundo=Imobiliario&aba=abaDocumento&idioma=pt-br' % ticker[0:4]
    req = Request(fii_url)
    try:
        response = urlopen(req)
    except HTTPError as e:
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
    except URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
    else:
#         print 'Host: %s' % (req.get_host())
        data = response.read()
        if 'Sistema indisponivel' in data:
            if num_tentativas == 3:
                raise ValueError(u'O sistema está indisponível')
            return buscar_rendimentos_fii_antigos(ticker, num_tentativas+1)
        inicio = data.find('<div id="tbArqListados">')
#         print 'inicio', inicio
        fim = data.find('</div>', inicio)
        string_importante = (data[inicio:fim])
#         http://bvmf.bmfbovespa.com.br/sig/FormConsultaPdfDocumentoFundos.asp?strSigla=BBPO&amp;strData=
        info_documentos = re.findall('<a[^>]*?href=\"([^>]*?)\"[^>]*?>Distribuiç.*?<span.*?>(.*?)</span>.*?</tr>', string_importante,flags=re.IGNORECASE|re.MULTILINE|re.DOTALL)
        info_documentos += re.findall('<a[^>]*?href=\"([^>]*?)\"[^>]*?>Amortizaç.*?<span.*?>(.*?)</span>.*?</tr>', string_importante,flags=re.IGNORECASE|re.MULTILINE|re.DOTALL)
#         print len(urls)
        for index, info in enumerate(reversed(info_documentos)):
            data_hora = datetime.datetime.strptime(info[0].split('strData=')[1], "%Y-%m-%dT%H:%M:%S.%f") 
            qtd_dias = (data_hora.date() - datetime.date(2010, 1, 1)).days
            qtd_mili = qtd_dias * 24 * 3600 * 1000 + data_hora.hour * 3600 * 1000 + data_hora.minute * 60 * 1000 \
                + data_hora.second * 1000 + int(info[0].split('strData=')[1].split('.')[1])
            protocolo = 'A' + str(hex(qtd_mili))[2:-1]
            informacoes_rendimentos.append({'url': info[0].replace('&amp;', '&'), 'data_ref': info[1], 'ticker': ticker, 'tipo': 'Aviso aos Cotistas', 'protocolo': protocolo})
    
def buscar_rendimentos_fii(ticker, ano_inicial, num_tentativas):
    """
    Busca distribuições de rendimentos de FII no formato atual no site da Bovespa
    """
    # Pesquisar no novo formato
    fii_url = 'http://bvmf.bmfbovespa.com.br/Fundos-Listados/FundosListadosDetalhe.aspx?Sigla=%s&tipoFundo=Imobiliario&aba=tabInformacoesRelevantes&idioma=pt-br' % ticker[0:4]
    # Usar mechanize para simular clique do usuario no javascript
    br = mechanize.Browser()
    br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    response = br.open(fii_url)
    
    response.read()

    try:
        br.select_form(nr=0)
        br.set_all_readonly(False)
        if not 'ctl00_contentPlaceHolderConteudo_ucInformacoesRelevantes_txtPeriodoDe' in [control.id for control in br.form.controls]:
            br.find_control("ctl00$botaoNavegacaoVoltar").disabled = True
            br.find_control(id='ctl00_contentPlaceHolderConteudo_ucInformacoesRelevantes_cmbAno').value = ['2016']
            response = br.submit()
            response.read()
    #     try:
        br.select_form(nr=0)
        br.set_all_readonly(False)
        br.find_control("ctl00$botaoNavegacaoVoltar").disabled = True
        br.find_control(id='ctl00_contentPlaceHolderConteudo_ucInformacoesRelevantes_txtPeriodoDe').value = '01/01/%s' % (ano_inicial)
        br.find_control(id='ctl00_contentPlaceHolderConteudo_ucInformacoesRelevantes_txtPeriodoAte').value = time.strftime("%d/%m/%Y")
        br.find_control(id='ctl00_contentPlaceHolderConteudo_ucInformacoesRelevantes_ddlCategoria').value = ['0']
    except ControlNotFoundError:
        if num_tentativas == 3:
            raise ValueError(u'Não encontrou os controles')
        return buscar_rendimentos_fii(ticker, ano_inicial, num_tentativas+1)
    
    response = br.submit()
    html = response.read()
    if 'Sistema indisponivel' in html:
        if num_tentativas == 3:
            raise ValueError(u'O sistema está indisponível')
        return buscar_rendimentos_fii(ticker, ano_inicial, num_tentativas+1)
    
    inicio = html.find('<div id="ctl00_contentPlaceHolderConteudo_ucInformacoesRelevantes_conteudoDetalhes">')
    fim = html.find('<script', inicio)
    string_importante = (html[inicio:fim])
    
    infos = re.findall('Data Referência:.*?(\d{2}/\d{2}/\d{4}).*?<tr><td>Assunto:</td><td>[^<]*(?:Distribuiç|Rendimento|Amortizaç)[^<]*</td></tr>.*?<a href=\"(https://fnet.bmfbovespa.com.br/fnet/publico/downloadDocumento\?id=[\d]*?)\">(.*?)</a>', string_importante,flags=re.IGNORECASE|re.DOTALL)

    for info in infos:
#         print info, ticker
        informacoes_rendimentos.append({'url': info[1], 'data_ref': info[0], 'ticker': ticker, 'tipo': info[2], 'protocolo': info[1].split('id=')[1]})
    