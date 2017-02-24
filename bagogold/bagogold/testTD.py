# -*- coding: utf-8 -*-
from bagogold.bagogold.models.td import HistoricoTitulo, Titulo, \
    ValorDiarioTitulo
from bagogold.bagogold.utils.td import criar_data_inicio_titulos
from decimal import Decimal
from urllib2 import Request, urlopen, URLError, HTTPError
import cgi
import datetime
import mechanize
import pyexcel
import pyexcel.ext.xls
import pytz
import re
import time



def baixar_historico_td_total():
    """
    Baixa o histórico de todos os títulos para todos os anos
    """
#     td_url = 'http://www.tesouro.fazenda.gov.br/tesouro-direto-balanco-e-estatisticas'
    td_url = 'http://sisweb.tesouro.gov.br/apex/f?p=2031:2'
    url_base = 'http://sisweb.tesouro.gov.br/apex/'
    
    # Usar mechanize para simular clique do usuario no javascript
    br = mechanize.Browser()
    br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    response = br.open(td_url)
    
    data = response.read()
    
    inicio = data.find('Histórico de preços e taxas')
    fim = data.find('</div>', inicio)
    string_importante = data[inicio:fim]
#     print string_importante
    
    urls = re.findall('href="(.*?)"', string_importante)
    for url in urls:
        url = url_base + url
        response_xls = urlopen(url)
        _, params = cgi.parse_header(response_xls.headers.get('Content-Disposition', ''))
        filename = params['filename']
        print 'Downloading %s from %s' % (filename, url)
        
        xls = response_xls.read()
        
        book = pyexcel.get_book(file_type="xls", file_content=xls, name_columns_by_row=0)
        sheets = book.to_dict()
        for key in sheets.keys():
            titulo_vencimento = sheets[key]
            espaco = ' '
            tipo = espaco.join(key.split(' ')[0 : len(key.split(' '))-1])
            data = time.strptime(key.split(' ')[len(key.split(' '))-1][0:4] + '20' + key.split(' ')[len(key.split(' '))-1][4:], "%d%m%Y")
            data = time.strftime('%Y-%m-%d', data)
#                 print(data)
            try:
                titulo = Titulo.objects.get(tipo=tipo, data_vencimento=data)
            except Titulo.DoesNotExist:
                titulo = Titulo(tipo=tipo, data_vencimento=data, data_inicio=data)
                titulo.save()
            for linha in range(2,len(titulo_vencimento)):
                # Testar se a linha de data está vazia, passar ao proximo
                if titulo_vencimento[linha][0] == '':
                    break
#                     print('Data: %s... type: %s' % (titulo_vencimento[linha][0], type(titulo_vencimento[linha][0])))
                
                # Formatar data
                if isinstance(titulo_vencimento[linha][0], (str, unicode)):
                    data_formatada = time.strptime(titulo_vencimento[linha][0], "%d/%m/%Y")
                    data_formatada = time.strftime('%Y-%m-%d', data_formatada)
                else:
                    data_formatada = time.strftime('%Y-%m-%d', titulo_vencimento[linha][0].timetuple())
                if data_formatada >= data:
                    break
                # Testar se os valores estao ok
                if not HistoricoTitulo.objects.filter(titulo=titulo, data=data_formatada).exists():
                    try:
                        float(titulo_vencimento[linha][1])
                        float(titulo_vencimento[linha][2])
                        float(titulo_vencimento[linha][3])
                        float(titulo_vencimento[linha][4])
                    except ValueError:
                        pass
                    else:
                        historico = HistoricoTitulo(titulo=titulo, data=data_formatada, taxa_compra=titulo_vencimento[linha][1]*100, taxa_venda=titulo_vencimento[linha][2]*100,
                                                    preco_compra=titulo_vencimento[linha][3], preco_venda=titulo_vencimento[linha][4])
                        historico.save()

def baixar_historico_td_ano(ano):
    """
    Baixa o histórico de todos os títulos para um ano
    Parâmetro: ano (inteiro ou string)
    """
#     td_url = 'http://www.tesouro.fazenda.gov.br/tesouro-direto-balanco-e-estatisticas'
    td_url = 'http://sisweb.tesouro.gov.br/apex/f?p=2031:2'
    url_base = 'http://sisweb.tesouro.gov.br/apex/'
    
    # Usar mechanize para simular clique do usuario no javascript
    br = mechanize.Browser()
    br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    response = br.open(td_url)
    
    data = response.read()
    
    inicio = data.find('Histórico de preços e taxas')
    fim = data.find('</div>', inicio)
    string_importante = data[inicio:fim]
#     print string_importante
    
    urls = re.findall('href="(.*?)"', string_importante)
    for url in urls:
        url = url_base + url
#         if str(ano) in url:
        response_xls = urlopen(url)
        _, params = cgi.parse_header(response_xls.headers.get('Content-Disposition', ''))
        filename = params['filename']
#         print 'Downloading %s from %s' % (filename, url)
        
        if str(ano) in filename:
            xls = response_xls.read()
            
            book = pyexcel.get_book(file_type="xls", file_content=xls, name_columns_by_row=0)
            sheets = book.to_dict()
            for key in sheets.keys():
                titulo_vencimento = sheets[key]
                espaco = ' '
                tipo = espaco.join(key.split(' ')[0 : len(key.split(' '))-1])
                data = time.strptime(key.split(' ')[len(key.split(' '))-1][0:4] + '20' + key.split(' ')[len(key.split(' '))-1][4:], "%d%m%Y")
                data = time.strftime('%Y-%m-%d', data)
    #                 print(data)
                try:
                    titulo = Titulo.objects.get(tipo=tipo, data_vencimento=data)
                except Titulo.DoesNotExist:
                    titulo = Titulo(tipo=tipo, data_vencimento=data, data_inicio=data)
                    titulo.save()
                for linha in range(2,len(titulo_vencimento)):
                    # Testar se a linha de data está vazia, passar ao proximo
                    if titulo_vencimento[linha][0] == '':
                        break
    #                     print('Data: %s... type: %s' % (titulo_vencimento[linha][0], type(titulo_vencimento[linha][0])))
                    
                    # Formatar data
                    if isinstance(titulo_vencimento[linha][0], (str, unicode)):
                        data_formatada = time.strptime(titulo_vencimento[linha][0], "%d/%m/%Y")
                        data_formatada = time.strftime('%Y-%m-%d', data_formatada)
                    else:
                        data_formatada = time.strftime('%Y-%m-%d', titulo_vencimento[linha][0].timetuple())
                    if data_formatada >= data:
                        break
                    # Testar se os valores estao ok
                    if not HistoricoTitulo.objects.filter(titulo=titulo, data=data_formatada).exists():
                        try:
                            float(titulo_vencimento[linha][1])
                            float(titulo_vencimento[linha][2])
                            float(titulo_vencimento[linha][3])
                            float(titulo_vencimento[linha][4])
                        except ValueError:
                            pass
                        else:
                            historico = HistoricoTitulo(titulo=titulo, data=data_formatada, taxa_compra=titulo_vencimento[linha][1]*100, taxa_venda=titulo_vencimento[linha][2]*100,
                                                        preco_compra=titulo_vencimento[linha][3], preco_venda=titulo_vencimento[linha][4])
                            historico.save()
                    
def remover_titulos_duplicados():
    titulos = Titulo.objects.all()
    for titulo in titulos:
#         print '%s %s %s' % (titulo, titulo.data_vencimento, titulo.id)
        outros_titulos = Titulo.objects.filter(tipo=titulo.tipo, data_vencimento=titulo.data_vencimento)
        for outro in outros_titulos:
            if outro.id != titulo.id:
                print 'Outro: %s %s %s' % (outro, outro.data_vencimento, outro.id)
                historicos = HistoricoTitulo.objects.filter(titulo__id=outro.id)
                for historico in historicos:
                    historico.titulo = titulo
                    historico.save()
                outro.delete()

def buscar_valores_diarios():
    td_url = 'http://www.tesouro.fazenda.gov.br/tesouro-direto-precos-e-taxas-dos-titulos'
    req = Request(td_url)
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
        string_importante = data[data.find('mercadostatus'):
                                 data.find('Descubra o título mais indicado para você')]
        string_compra = string_importante[:string_importante.rfind('mercadostatus')]
        linhas = re.findall('<tr class="[^"]*?camposTesouroDireto[^"]*?">.*?</tr>', string_compra)
        contador = 0
        valores_diarios = []
        for linha in linhas:
            campos = re.findall('<td.*?>.*?</td>', linha)
            tipo_titulo = ''
            valor_diario = ValorDiarioTitulo()
            for campo in campos:
                # Parte importante da coluna para o preenchimento dos valores
                dado = re.sub(r'<.*?>', "", campo).strip()
#                 print dado
                if contador == 0:
                    tipo_titulo = re.findall('\(.*?\)', dado)[0]
#                     print tipo_titulo
                    tipo_titulo = tipo_titulo.replace('(', '').replace(')', '')
                    if tipo_titulo == 'NTNB Princ':
                        tipo_titulo = 'NTN-B Principal'
                    elif tipo_titulo == 'NTNB':
                        tipo_titulo = 'NTN-B'
                    elif tipo_titulo == 'NTNF':
                        tipo_titulo = 'NTN-F'
                    elif tipo_titulo == 'NTNC':
                        tipo_titulo = 'NTN-C'
                elif contador == 1:
                    data_formatada = time.strptime(dado, "%d/%m/%Y")
                    data_formatada = time.strftime('%Y-%m-%d', data_formatada)
                    valor_diario.titulo = Titulo.objects.get(tipo=tipo_titulo, data_vencimento=data_formatada)
                elif contador == 2:
                    valor_diario.taxa_compra = Decimal(re.sub(r'[^\d\.]', '', dado.replace('.', '').replace(',', '.')))
                elif contador == 4:
                    valor_diario.preco_compra = Decimal(re.sub(r'[^\d\.]', '', dado.replace('.', '').replace(',', '.')))
                    valores_diarios += [valor_diario]
                # Garante o posicionamento
                contador += 1
                if contador == 5:
                    contador = 0
        string_venda = string_importante[string_importante.rfind('mercadostatus'):]
        linhas = re.findall('<tr class="[^"]*?camposTesouroDireto[^"]*?">.*?</tr>', string_venda)
        contador = 0
        for linha in linhas:
            campos = re.findall('<td.*?>.*?</td>', linha)
            tipo_titulo = ''
            valor_diario = ValorDiarioTitulo()
            for campo in campos:
                # Parte importante da coluna para o preenchimento dos valores
                dado = re.sub(r'<.*?>', "", campo).strip()
#                 print dado
                if contador == 0:
                    tipo_titulo = re.findall('\(.*?\)', dado)[0]
#                     print tipo_titulo
                    tipo_titulo = tipo_titulo.replace('(', '').replace(')', '')
                    if tipo_titulo == 'NTNB Princ':
                        tipo_titulo = 'NTN-B Principal'
                    elif tipo_titulo == 'NTNB':
                        tipo_titulo = 'NTN-B'
                    elif tipo_titulo == 'NTNF':
                        tipo_titulo = 'NTN-F'
                    elif tipo_titulo == 'NTNC':
                        tipo_titulo = 'NTN-C'
                elif contador == 1:
                    data_formatada = time.strptime(dado, "%d/%m/%Y")
                    data_formatada = time.strftime('%Y-%m-%d', data_formatada)
                    valor_diario.titulo = Titulo.objects.get(tipo=tipo_titulo, data_vencimento=data_formatada)
                    if valor_diario.titulo in [valor_preenchido.titulo for valor_preenchido in valores_diarios]:
                        valor_diario = [valor_preenchido for valor_preenchido in valores_diarios if valor_preenchido.titulo == valor_diario.titulo][0]
                elif contador == 2:
                    valor_diario.taxa_venda = Decimal(re.sub(r'[^\d\.]', '', dado.replace('.', '').replace(',', '.')))
                elif contador == 3:
                    valor_diario.preco_venda = Decimal(re.sub(r'[^\d\.]', '', dado.replace('.', '').replace(',', '.')))
                    if valor_diario.titulo not in [valor_preenchido.titulo for valor_preenchido in valores_diarios]:
                        valores_diarios += [valor_diario]
                # Garante o posicionamento
                contador += 1
                if contador == 4:
                    contador = 0
        # Buscar data e hora do valor
        data_hora = re.findall('Atualizado em:.*?</b>', string_importante)[0]
        data_hora = re.findall('<b>.*?</b>', data_hora)[0]
        data_hora = re.sub(r'<.*?>', "", data_hora).strip()
        data = data_hora.split(' ')[0]
        hora = data_hora.split(' ')[1]
        data_hora_formatada = datetime.datetime(int(data.split('/')[2]), int(data.split('/')[1]), int(data.split('/')[0]), 
                                                int(hora.split(':')[0]), int(hora.split(':')[1]), 0, 0, pytz.UTC)
        for valor_diario in valores_diarios:
            valor_diario.data_hora = data_hora_formatada
            
            # Verifica se algum dos preços e taxas é nulo, transformando em 0
            if valor_diario.preco_compra == None:
                valor_diario.preco_compra = 0
            if valor_diario.taxa_compra == None:
                valor_diario.taxa_compra = 0
            if valor_diario.preco_venda == None:
                valor_diario.preco_venda = 0
            if valor_diario.taxa_venda == None:
                valor_diario.taxa_venda = 0
        return valores_diarios