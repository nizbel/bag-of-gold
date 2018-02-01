def gerar_sitemap():
    # Trabalhar sempre com (url, qtd_vezes_encontrada)
    url_inicial = reverse('inicio:painel_geral')
    lista_urls = [url_inicial]
    
    lista_urls_encontradas = {url_inicial: 0}
    while len(lista_urls) > 0:
        url = lista_urls.pop()
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        page = response.read()
        
        urls_page = re.findall('(http|https)://([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?', page)
        for url_encontrada in [url_page for url_page in urls_page if 'static' not in url_page and '?' not in url_page]:
            if url_encontrada in lista_urls_encontradas.keys():
                lista_urls_encontradas[url_encontrada] += 1
            else:
                lista_urls.append(url_encontrada)
                lista_urls_encontradas[url_encontrada] = 0
                
    # Gerar arquivo
    sitemap = file('sitemap.xml', 'w+')
    qtd_maxima_encontrada = max(lista_urls_encontradas.values())
    for url, qtd in lista_urls_encontradas.items():
        sitemap.write('<url><loc>%s</loc><frequency>weekly</frequency><relevance>%s</relevance>' % (url, qtd/qtd_maxima_encontrada))
        
        