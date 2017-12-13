# -*- coding: utf-8 -*-
from bagogold.bagogold.models.empresa import Empresa
from mechanize._form import ControlNotFoundError
from urllib2 import urlopen
from StringIO import StringIO
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
    
def buscar_historico_recente_bovespa():
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
        br.find_control("chkArquivoDownload_ativo").disabled = False
        br.find_control("chkArquivoDownload_ativo").items[27].selected = True
        response = br.submit()
        
#         fileobj = open("teste.ex_","w+")
#         fileobj.write(response.read())
#         fileobj.close()
        
        arquivo_zipado = StringIO(response.read())
        unzipped = zipfile.ZipFile(arquivo_zipado)
            
        ult_arq_zip = max(unzipped.namelist())
        # Ler arquivo mais recente
        file(ult_arq_zip,'wb').write(unzipped.read(ult_arq_zip))
        
        return ult_arq_zip
            
    except ControlNotFoundError:
        raise ValueError(u'Não encontrou os controles')
    
#     if 'Sistema indisponivel' in html:
#         raise ValueError(u'O sistema está indisponível')
