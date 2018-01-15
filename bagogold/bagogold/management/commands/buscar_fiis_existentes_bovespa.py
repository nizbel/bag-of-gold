# -*- coding: utf-8 -*-
from bagogold.bagogold.models.empresa import Empresa
from bagogold.bagogold.models.fii import FII
from bagogold.bagogold.utils.bovespa import preencher_empresa_fii_nao_listado
from django.core.management.base import BaseCommand
from threading import Thread
from urllib2 import Request, urlopen, HTTPError, URLError
import re
import sys
import time

# A thread 'Principal' indica se ainda está rodando a thread principal
threads_rodando = {'Principal': 1}
fiis_para_verificar = list()

class VerificarFIIThread(Thread):
    def run(self):
        try:
            while len(threads_rodando) > 0 or len(fiis_para_verificar) > 0:
                while len(fiis_para_verificar) > 0:
                    sigla, ticker, empresa_nome, empresa_nome_pregao = fiis_para_verificar.pop(0)
                    
                    # Testa se empresa não existia
                    if not Empresa.objects.filter(codigo_cvm=sigla).exists():
                        empresa = Empresa(nome=empresa_nome, codigo_cvm=sigla, nome_pregao=empresa_nome_pregao)
                        empresa.save()
                    
                    # FII existia
                    if FII.objects.filter(ticker=ticker).exists():
                        fii = FII.objects.get(ticker=ticker)
                        if not fii.empresa:
                            fii.empresa = empresa
                            fii.save()
                    else:
                        fii = FII(ticker=ticker, empresa=empresa)
                        fii.save()
                time.sleep(10)
        except Exception as e:
#             template = "An exception of type {0} occured. Arguments:\n{1!r}"
#             message = template.format(type(e).__name__, e.args)
#             print message
            pass
                
class BuscaTickerThread(Thread):
    def __init__(self, sigla, empresa_nome, empresa_nome_pregao):
        self.sigla = sigla 
        self.empresa_nome = empresa_nome
        self.empresa_nome_pregao = empresa_nome_pregao
        super(BuscaTickerThread, self).__init__()

    def run(self):
        try:
            cod_negociacao = busca_ticker(self.sigla, 0)
            if cod_negociacao:
                fiis_para_verificar.append((self.sigla, cod_negociacao, self.empresa_nome, self.empresa_nome_pregao))
        except Exception as e:
#             template = "An exception of type {0} occured. Arguments:\n{1!r}"
#             message = template.format(type(e).__name__, e.args)
#             print self.sigla, "Thread:", message
            pass
        # Tenta remover seu código da listagem de threads até conseguir
        while self.sigla in threads_rodando:
            del threads_rodando[self.sigla]

class Command(BaseCommand):
    help = 'Busca FIIs listados na bovespa'

    def add_arguments(self, parser):
        parser.add_argument('--n', action='store_true')
        
    def handle(self, *args, **options):
        fiis = verificar_fiis_listados()
        
        qtd_threads = 12
        contador = 0
        
        # Prepara thread de geração de info para documento
        thread_verificar_fii = VerificarFIIThread()
        thread_verificar_fii.start()
        
#         start_time = time.time()
        try:
            while contador < len(fiis):
                fii = fiis[contador]
                t = BuscaTickerThread(fii[2], fii[0], fii[1])
                threads_rodando[fii[2]] = 1
                t.start()
                contador += 1
                while (len(threads_rodando) > qtd_threads):
#                     print 'FIIs para verificar:', len(fiis_para_verificar), '... Threads:', len(threads_rodando), contador
                    time.sleep(3)
            while (len(threads_rodando) > 0 or len(fiis_para_verificar) > 0):
#                 print 'FIIs para verificar:', len(fiis_para_verificar), '... Threads:', len(threads_rodando), contador
                while 'Principal' in threads_rodando.keys():
                    del threads_rodando['Principal']
                time.sleep(3)
        except KeyboardInterrupt:
#             print 'FIIs para verificar:', len(fiis_para_verificar), '... Threads:', len(threads_rodando), contador
            while 'Principal' in threads_rodando.keys():
                del threads_rodando['Principal']
                time.sleep(3)
#         print time.time() - start_time
        if options['n']:
            # Buscar não listados
            for fii in FII.objects.filter(empresa__isnull=True):
                try:
                    preencher_empresa_fii_nao_listado(fii.ticker)
                    fii.empresa = Empresa.objects.get(codigo_cvm=fii.ticker[0:4])
                    fii.save()
                except Exception as e:
                    print 'Erro no FII', fii.ticker, e

def verificar_fiis_listados():
#     http://bvmf.bmfbovespa.com.br/Fundos-Listados/FundosListadosDetalhe.aspx?Sigla=AEFI&tipoFundo=Imobiliario&aba=abaPrincipal&idioma=pt-br
    # Verificar fiis listados
    fii_url = 'http://bvmf.bmfbovespa.com.br/Fundos-Listados/FundosListados.aspx?tipoFundo=imobiliario&amp;Idioma=pt-br'
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
        data = response.read().decode('utf-8')
        string_importante = (data[data.find('<table>'):data.find('</table>')])
        return re.findall('<a.*?>(.+?)</a>.*?<a.*?>(.+?)</a>.*?<td>.*?</td>.*?<td><span.*?>(.+?)</span></td>.*?</tr>', string_importante, flags=re.DOTALL)
        
def busca_ticker(sigla, num_tentativas):
    sigla_url = 'http://bvmf.bmfbovespa.com.br/Fundos-Listados/FundosListadosDetalhe.aspx?Sigla=%s&tipoFundo=Imobiliario&aba=abaPrincipal&idioma=pt-br' % (sigla)
    resposta = urlopen(sigla_url)
    string_retorno = resposta.read()
    if 'Sistema indisponivel' in string_retorno:
        if num_tentativas == 3:
            raise ValueError('Excedeu número de tentativas')
        busca_ticker(sigla, num_tentativas+1)
        return
    string_importante = string_retorno[string_retorno.find('Códigos de Negociação'):string_retorno.find('CNPJ')]
    if '</a>' in string_importante:
        cod_negociacao = re.sub(r'.*?<a.*?>(.*?)<\/a>.*', r'\1', string_importante, flags=re.DOTALL)
#         print sigla, ": ", cod_negociacao
        return cod_negociacao
    else:
        return ''