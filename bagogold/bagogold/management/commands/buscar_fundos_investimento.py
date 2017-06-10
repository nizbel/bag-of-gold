# -*- coding: utf-8 -*-
from StringIO import StringIO
from bagogold import settings
from bagogold.bagogold.utils.misc import verificar_feriado_bovespa, \
    ultimo_dia_util, buscar_dia_util_aleatorio
from bagogold.fundo_investimento.models import FundoInvestimento, Administrador, \
    DocumentoCadastro, LinkDocumentoCadastro
from django.core.mail import mail_admins
from django.core.management.base import BaseCommand
from django.db import transaction
from lxml import etree
from urllib2 import urlopen
import datetime
import os
import random
import time
import traceback
import zeep
import zipfile

class Command(BaseCommand):
    help = 'Buscar fundos de investimento na CVM'

    def add_arguments(self, parser):
        parser.add_argument('--aleatorio', action='store_true')

    def handle(self, *args, **options):        
        try:
            wsdl = 'http://sistemas.cvm.gov.br/webservices/Sistemas/SCW/CDocs/WsDownloadInfs.asmx?WSDL'
            client = zeep.Client(wsdl=wsdl)
            resposta = client.service.Login(2377, '16335')
            headerSessao = resposta['header']
    #         print headerSessao
        
            dias_uteis = list()
            if not options['aleatorio']:
                # Buscar último dia útil
                dias_uteis.append(ultimo_dia_util())
            else:
                # Buscar dias úteis que não tenham sido inseridos previamente
                for _ in range(5):
                    dia_util = buscar_dia_util_aleatorio(datetime.date(2002, 1 ,1), ultimo_dia_util())
                    while DocumentoCadastro.objects.filter(data_referencia=dia_util, leitura_realizada=True).exists():
                        dia_util = buscar_dia_util_aleatorio(datetime.date(2002, 1 ,1), ultimo_dia_util())
                    dias_uteis.append(dia_util)
                
                
            # Busca de competencias
            for dia_util in dias_uteis:
                # Testa se já não foi criado o link para o documento (apenas para não aleatório pois o aleatório evita datas já cadastradas)
                if not DocumentoCadastro.objects.filter(data_referencia=dia_util).exists():
                    try:
                        with transaction.atomic():
                            respostaCompetencias = client.service.solicAutorizDownloadCadastro(dia_util, 'Teste', _soapheaders=[headerSessao])
                            # Criar documento
                            novo_documento = DocumentoCadastro.objects.create(data_referencia=dia_util, data_pedido_cvm=datetime.date.today())
                            url = respostaCompetencias['body']['solicAutorizDownloadCadastroResult']
                            # Criar link
                            LinkDocumentoCadastro.objects.create(url=url, documento=novo_documento)
                    except zeep.exceptions.Fault as erro_wsdl:
                        # Verifica se não encontrou arquivo para os parâmetros
                        if u'Arquivo para download não encontrado para os parâmetros especificados' in erro_wsdl:
                            # Nesse caso, verificar se é a busca aleatoria para adicionar mais uma data para dias_uteis 
                            if options['aleatorio']:
                                dia_util = buscar_dia_util_aleatorio(datetime.date(2002, 1 ,1), ultimo_dia_util())
                                while DocumentoCadastro.objects.filter(data_referencia=dia_util).exists():
                                    dia_util = buscar_dia_util_aleatorio(datetime.date(2002, 1 ,1), ultimo_dia_util())
                                dias_uteis.append(dia_util)
                        else:
                            if settings.ENV == 'DEV':
                                print traceback.format_exc()
                            elif settings.ENV == 'PROD':
                                mail_admins(u'Erro em Buscar fundos investimento', u'%s aconteceu para dia %s' % (erro_wsdl, dia_util.strftime('%d/%m/%Y')))
                        continue
                else:
                    documento_cadastro = DocumentoCadastro.objects.get(data_referencia=dia_util)
                    if not documento_cadastro.leitura_realizada:
                        # Se não for do mesmo dia, gerar novo
                        if (datetime.date.today() - documento_cadastro.data_pedido_cvm).days > 0:
                            try:
                                respostaCompetencias = client.service.solicAutorizDownloadCadastro(dia_util, 'Teste', _soapheaders=[headerSessao])
                                url = respostaCompetencias['body']['solicAutorizDownloadCadastroResult']
                                # Atualizar link
                                link = LinkDocumentoCadastro.objects.get(documento=novo_documento)
                                link.url = url
                                link.save()
                            except zeep.exceptions.Fault as erro_wsdl:
                                # Verifica se não encontrou arquivo para os parâmetros
                                if u'Arquivo para download não encontrado para os parâmetros especificados' in erro_wsdl:
                                    # Nesse caso, verificar se é a busca aleatoria para adicionar mais uma data para dias_uteis 
                                    if options['aleatorio']:
                                        dia_util = buscar_dia_util_aleatorio(datetime.date(2002, 1 ,1), ultimo_dia_util())
                                        while DocumentoCadastro.objects.filter(data_referencia=dia_util).exists():
                                            dia_util = buscar_dia_util_aleatorio(datetime.date(2002, 1 ,1), ultimo_dia_util())
                                        dias_uteis.append(dia_util)
                                else:
                                    if settings.ENV == 'DEV':
                                        print traceback.format_exc()
                                    elif settings.ENV == 'PROD':
                                        mail_admins(u'Erro em Buscar fundos investimento', u'%s aconteceu para dia %s' % (erro_wsdl, dia_util.strftime('%d/%m/%Y')))
                                continue
                        else:
                            # Mesmo dia, pegar link cadastrado
                            url = LinkDocumentoCadastro.objects.get(documento__data_referencia=dia_util).url
                    else:
                        url = LinkDocumentoCadastro.objects.get(documento__data_referencia=dia_util).url
#                 url = 'http://cvmweb.cvm.gov.br/swb/sistemas/scw/DownloadArqs/LeDownloadArqs.aspx?VL_GUID=8fc00daf-4fc8-4d83-bc4c-3e45cc79576c&PK_SESSAO=963322175&PK_ARQ_INFORM_DLOAD=196451'
                # Tenta extrair arquivo, se não conseguir, continua com o próximo
                try:
                    download = urlopen(url)
                    arquivo_zipado = StringIO(download.read())
                    unzipped = zipfile.ZipFile(arquivo_zipado)
                except:
                    if settings.ENV == 'DEV':
                        print traceback.format_exc()
                    elif settings.ENV == 'PROD':
                        mail_admins(u'Erro em Buscar fundos investimento na data %s' % (dia_util.strftime('%d/%m/%Y')), traceback.format_exc())
                    continue
                for libitem in unzipped.namelist():
                    try:
                        # Ler arquivo
                        file(libitem,'wb').write(unzipped.read(libitem))
                        arquivo_cadastro = file(libitem, 'r')
                        tree = etree.parse(arquivo_cadastro)
                        if not options['aleatorio']:
                            fundos = list()
                        # Definir campos para traceback
                        campos = None
                        with transaction.atomic():
                            # Lê o arquivo procurando nós CADASTRO (1 para cada fundo)
                            for element in tree.getroot().iter('CADASTRO'):
                                campos = {key: value for (key, value) in [(elemento.tag, elemento.text) for elemento in element.iter()]}
                                # Verificar se administrador já existe
                                if not Administrador.objects.filter(cnpj=campos['CNPJ_ADMINISTRADOR']).exists():
                                    novo_administrador = Administrador(nome=campos['NOME_ADMINISTRADOR'].strip(), cnpj=campos['CNPJ_ADMINISTRADOR'].strip())
                                    novo_administrador.save()
                                 
                                # Verificar se fundo já existe
                                if not FundoInvestimento.objects.filter(cnpj=campos['CNPJ']).exists():
                                    novo_fundo = FundoInvestimento(cnpj=campos['CNPJ'].strip(), nome=campos['NOME'].strip(), administrador=Administrador.objects.get(cnpj=campos['CNPJ_ADMINISTRADOR']),
                                                                   data_constituicao=campos['DT_CONSTITUICAO'].strip(), situacao=FundoInvestimento.buscar_tipo_situacao(campos['SITUACAO']), 
                                                                   tipo_prazo=definir_prazo__pelo_cadastro(campos['TRATAMENTO_TRIBUTARIO']),
                                                                   classe=FundoInvestimento.buscar_tipo_classe(campos['CLASSE']), exclusivo_qualificados=(campos['INVESTIDORES_QUALIFICADOS'].strip().upper() == 'SIM'),
                                                                   ultimo_registro=dia_util)
                                    novo_fundo.save()
                                else:
                                    # Verificar se houve alteração no fundo
                                    fundo = FundoInvestimento.objects.get(cnpj=campos['CNPJ'])
                                    if fundo.ultimo_registro < dia_util:
                                        fundo.ultimo_registro = dia_util
                                        # Verificar alteração de administrador
                                        if campos['CNPJ_ADMINISTRADOR'] != fundo.administrador.cnpj:
                                            fundo.administrador = Administrador.objects.get(cnpj=campos['CNPJ_ADMINISTRADOR'])
                                        if campos['SITUACAO'] != None and campos['SITUACAO'] != fundo.descricao_situacao():
                                            fundo.situacao = FundoInvestimento.buscar_tipo_situacao(campos['SITUACAO'])
                                        if campos['CLASSE'] != None and campos['CLASSE'] != fundo.descricao_classe():
                                            fundo.classe = FundoInvestimento.buscar_tipo_classe(campos['CLASSE'])
                                        if campos['NOME'] != None and campos['NOME'].strip() != fundo.nome:
                                            fundo.nome = campos['NOME'].strip()
                                        fundo.save()
                                    
                                # Adicionar a lista de fundos para comparar posteriormente
                                if not options['aleatorio']:
                                    fundos.append(campos['CNPJ'])
                                
#                                 print novo_fundo             
                            documento = DocumentoCadastro.objects.get(data_referencia=dia_util)  
                            documento.leitura_realizada = True
                            documento.save()             
                        os.remove(libitem)                                
                    except:
                        # Apagar arquivo caso haja erro, enviar mensagem para email
                        os.remove(libitem)
                        if settings.ENV == 'DEV':
                            print traceback.format_exc()
                        elif settings.ENV == 'PROD':
                            mail_admins(u'Erro em Buscar fundos investimento na data %s' % (dia_util.strftime('%d/%m/%Y')), traceback.format_exc())
                # Verificar fundos que existem porém não foram listados, ou seja, estão terminados
                if not options['aleatorio']:
                    # Verificar fundos não encontrados no cadastro para terminar
                    for fundo in FundoInvestimento.objects.all().exclude(situacao=FundoInvestimento.SITUACAO_TERMINADO):
                        if fundo.cnpj not in fundos:
                            fundo.situacao = FundoInvestimento.SITUACAO_TERMINADO
                            fundo.save()
        except:
            if settings.ENV == 'DEV':
                print traceback.format_exc()
            elif settings.ENV == 'PROD':
                mail_admins(u'Erro em Buscar fundos investimento', traceback.format_exc())

def definir_prazo__pelo_cadastro(str_tributacao_documento):
    if str_tributacao_documento == None:
        return FundoInvestimento.PRAZO_LONGO
    return FundoInvestimento.PRAZO_LONGO if str_tributacao_documento.strip().lower() == 'sim' else FundoInvestimento.PRAZO_CURTO