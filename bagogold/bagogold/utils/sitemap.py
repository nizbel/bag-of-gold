# -*- coding: utf-8 -*-
from bagogold import settings
from decimal import Decimal
from django.core.urlresolvers import reverse
import re
import urllib2

HOST_DEV = 'http://localhost:8000'
HOST_PROD = 'https://bagofgold.com.br'

def gerar_sitemap():
    if settings.ENV == 'DEV':
        host = HOST_DEV
    elif settings.ENV == 'PROD':
        host = HOST_PROD
    url_inicial = '%s%s' % (host, reverse('inicio:home'))
    lista_urls = [url_inicial]
    
    # Trabalhar sempre com (url, qtd_vezes_encontrada)
    lista_urls_encontradas = {url_inicial: 0}
    while len(lista_urls) > 0:
        url = lista_urls.pop(0)
        print len(lista_urls), url
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        page = response.read()
        
#         urls_page = re.findall('(http|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?', page)
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
                
    # Gerar arquivo
    sitemap = file('sitemap.xml', 'w+')
    sitemap.write('<?xml version="1.0" encoding="UTF-8"?>')
    sitemap.write('\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                  'xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9 http://www.sitemaps.org/schemas/sitemap/0.9/sitemap.xsd">')
    qtd_maxima_encontrada = max(lista_urls_encontradas.values())
    for url, qtd in lista_urls_encontradas.items():
        sitemap.write('\n<url><loc>%s</loc><changefreq>weekly</changefreq><priority>%s</priority></url>' % (url, 
                                                  (Decimal(qtd)/qtd_maxima_encontrada).quantize(Decimal('0.01'))))
    sitemap.write('\n</urlset>')
        
        