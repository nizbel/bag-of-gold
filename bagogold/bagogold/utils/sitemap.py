# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal
import re
from threading import Thread
import time
import urllib2

from django.core.urlresolvers import reverse

from bagogold import settings


HOST_DEV = 'http://localhost:8000'
HOST_PROD = 'https://bagofgold.com.br'

lista_urls = list()
paginas_encontradas = list()
# A thread 'Principal' indica se ainda está rodando a thread principal
threads_rodando = {'Principal': 1}

class BuscaPaginaThread(Thread):
    def __init__(self, identificador):
        self.identificador = identificador 
        super(BuscaPaginaThread, self).__init__()

    def run(self):
        inicio = datetime.datetime.now()
        try:
            while len(lista_urls) > 0 or len(paginas_encontradas) > 0 or (datetime.datetime.now() - inicio) < datetime.timedelta(seconds=10):
                if len(lista_urls) > 0:
                    url = lista_urls.pop(0)
                    print url
                    req = urllib2.Request(url)
                    response = urllib2.urlopen(req)
                    page = response.read()
                    # Interessam apenas links mostrados antes dos scripts (evitar ajax)
                    paginas_encontradas.append(page[page.find('<body') : page.find('<script')])
        except Exception as e:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(e).__name__, e.args)
            print self.identificador, "Thread:", message
#             pass
        # Tenta remover seu código da listagem de threads até conseguir
        while self.identificador in threads_rodando:
            del threads_rodando[self.identificador]

def gerar_sitemap():
    if settings.ENV == 'DEV':
        host = HOST_DEV
    elif settings.ENV == 'PROD':
        host = HOST_PROD
    url_inicial = '%s%s' % (host, reverse('inicio:home'))
    lista_urls.append(url_inicial)
    
    # Trabalhar sempre com (url, qtd_vezes_encontrada)
    lista_urls_encontradas = {}
    
    # Buscar URLs que possuem detalhamento
    for url in listar_urls_de_detalhamento():
        url_host = '%s%s' % (host, url)
        lista_urls.append(url_host)
        lista_urls_encontradas[url_host] = -1
    
    count = 1
    try:
        while len(lista_urls) > 0 or len(threads_rodando.keys()) > 1 or len(paginas_encontradas) > 0:
            if len(lista_urls) > 0 and len(threads_rodando.keys()) <= 2:
                t = BuscaPaginaThread(count)
                threads_rodando[count] = 1
                t.start()
                count += 1
            while len(paginas_encontradas) > 0:
        #         urls_page = re.findall('(http|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?', page)
                page = paginas_encontradas.pop(0)
                urls_page = re.findall('"/[-\d\w_/]*"', page)
                urls_page = ['%s%s' % (host, url_page.replace('"', '')) for url_page in urls_page]
                for url_encontrada in [url_page for url_page in urls_page if 'static' not in url_page and '?' not in url_page]:
                    # Se URL encontrada já havia sido encontrada antes, apenas incrementa quantidade de vezes vista
                    if url_encontrada in lista_urls_encontradas.keys():
                        lista_urls_encontradas[url_encontrada] += 1
                    # Caso contrário, adicionar a lista de encontradas com 1 encontro e preparar para verificá-la
                    else:
                        lista_urls.append(url_encontrada)
                        lista_urls_encontradas[url_encontrada] = 1
            print len(lista_urls), len(lista_urls_encontradas.keys())
            time.sleep(5)
        while 'Principal' in threads_rodando.keys():
            del threads_rodando['Principal']
        time.sleep(3)
    except KeyboardInterrupt:
#             print 'FIIs para verificar:', len(fiis_para_verificar), '... Threads:', len(threads_rodando), contador
        while 'Principal' in threads_rodando.keys():
            del threads_rodando['Principal']
            time.sleep(3)
    
    # Gerar arquivo
    sitemap = file('sitemap.xml', 'w+')
    sitemap.write('<?xml version="1.0" encoding="UTF-8"?>')
    sitemap.write('\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                  'xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9 http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">')
    qtd_maxima_encontrada = max(lista_urls_encontradas.values())
    for url, qtd in lista_urls_encontradas.items():
        prioridade = max((Decimal(qtd)/qtd_maxima_encontrada).quantize(Decimal('0.01')), Decimal('0.1'))
        sitemap.write('\n<url><loc>%s</loc><changefreq>weekly</changefreq><priority>%s</priority></url>' % (url, prioridade))
    sitemap.write('\n</urlset>')
        
def listar_urls_de_detalhamento():
    lista_urls = list()
    
    # Ações
    for acao in Acao.objects.all():
        lista_urls.append(reverse('acao:geral:detalhar_acao', kwargs={'ticker': acao.ticker}))
        
    # Debêntures
    for debenture in Debenture.objects.all():
        lista_urls.append(reverse('debenture:detalhar_debenture', kwargs={'id_debenture': debenture.id}))
        
    # FII
    for fii in FII.objects.all():
        lista_urls.append(reverse('fii:detalhar_fii', kwargs={'ticker': fii.ticker}))
        
    # Fundos de investimento
    for fundo in FundoInvestimento.objects.all():
        lista_urls.append(reverse('fundo_investimento:detalhar_fundo_investimento', kwargs={'fundo_slug': fundo.slug}))
        
#    # Tesouro Direto
#    for titulo in Titulo.objects.all():
#        lista_urls.append(reverse('tesouro_direto:detalhar_titulo_td', kwargs={'titulo_slug': titulo.slug}))
        
    return lista_urls