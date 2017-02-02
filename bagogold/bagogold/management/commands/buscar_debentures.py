# -*- coding: utf-8 -*-
from bagogold.bagogold.models.debentures import Debenture, JurosDebenture, \
    PremioDebenture, AmortizacaoDebenture
from decimal import Decimal
from django.core.management.base import BaseCommand
from threading import Thread
from urllib2 import Request, urlopen, HTTPError, URLError
import datetime
import re
import time

# A thread 'Principal' indica se ainda está rodando a thread principal
threads_rodando = {'Principal': 1}
debentures_para_processar = list()

class ProcessaDebentureThread(Thread):
    def run(self):
        try:
            while len(threads_rodando) > 0 or len(debentures_para_processar) > 0:
                while len(debentures_para_processar) > 0:
                    dados_debenture = debentures_para_processar.pop(0)
                    # Pegar a chave do primeiro registro pois é sempre enviado um dicionário de registro único
                    codigo = dados_debenture.keys()[0]
                    campos = dados_debenture[codigo]
                    
                    # É padrão SND?
                    padrao_snd = campos[43]
                    try:
                        if padrao_snd == u'Padrão - SND': 
                            # Data de emissão
                            data_emissao = datetime.datetime.strptime(campos[11], '%d/%m/%Y').date()
                            # Data de vencimento
                            data_vencimento = None if campos[12] == u'Indeterminado' else datetime.datetime.strptime(campos[12] , '%d/%m/%Y').date()
                            # Data de início de rendimento
                            data_inicio_rendimento = datetime.datetime.strptime(campos[15], '%d/%m/%Y').date()
                            # VNU de emissão
                            valor_nominal_emissao = campos[37]
                            # Índice
                            indice = campos[41]
                            if indice in [u'SELIC', u'PRÉ', u'IGP-M', u'IPCA', u'DI', u'PREFIXADO']:
                                # Alterar valor do índice para ser aceito nos tipos de indexação
                                if indice in [u'PRÉ',u'PREFIXADO']:
                                    indice = u'Prefixado'
                                # Buscar juros, amortização e prêmio
                                amortizacao_taxa = Decimal(re.sub('[^\d,\.]', '', campos[52]).replace(',', '.') or '0')
                                amortizacao_periodo = re.sub('[^\d]', '', campos[53]) or '0'
                                amortizacao_unidade = campos[54]
                                amortizacao_carencia = None if re.sub('[^\d/]', '', campos[55]) == '' else datetime.datetime.strptime(re.sub('[^\d/]', '', campos[55]), '%d/%m/%Y').date()
                                amortizacao_tipo = 0
                                for indice_amortizacao, tipo in [tipo for tipo in AmortizacaoDebenture.TIPOS_AMORTIZACAO]:
                                    if campos[57] == tipo:
                                        amortizacao_tipo = indice_amortizacao
                                        break
                                
                                juros_taxa = Decimal(re.sub('[^\d,\.]', '', campos[58]).replace(',', '.') or '0')
                                juros_periodo = re.sub('[^\d]', '', campos[60]) or '0'
                                juros_unidade = campos[61]
                                juros_carencia = None if re.sub('[^\d/]', '', campos[62]) == '' else datetime.datetime.strptime(re.sub('[^\d/]', '', campos[62]), '%d/%m/%Y').date()
                                
                                premio_taxa = Decimal(re.sub('[^\d,\.]', '', campos[65]).replace(',', '.') or '0')
                                premio_periodo = re.sub('[^\d]', '', campos[67]) or '0'
                                premio_unidade = campos[68]
                                premio_carencia = None if re.sub('[^\d/]', '', campos[69]) == '' else datetime.datetime.strptime(re.sub('[^\d/]', '', campos[69]), '%d/%m/%Y').date()
                            else:
                                raise ValueError(u'Tipo não previsto: %s' % (campos[41]))
                            # Percentual multiplicador do índice
                            percentual_indice = Decimal(re.sub('[^\d,\.]', '', campos[47]).replace(',', '.') or '100')
                            # Situação
                            situacao = campos[5]
                            # Data último VNU
                            data_saida = campos[40]
                            # É debenture incentivada?
                            incentivada = campos[88]
                      
                            if Debenture.objects.filter(codigo=codigo).exists():
                                debenture = Debenture.objects.get(codigo=codigo)
                                # TODO comparar se houve alteração
                            else:
                                debenture = Debenture(codigo=codigo)
                                
                            debenture.data_emissao = data_emissao
                            debenture.valor_emissao = valor_nominal_emissao.replace('.', '').replace(',', '.')
                            debenture.data_inicio_rendimento = data_inicio_rendimento
                            debenture.data_vencimento = data_vencimento
                            debenture.incentivada = False if 'N' in incentivada.upper() else True
                            debenture.padrao_snd = True
                            debenture.indice = debenture.buscar_codigo_tipo_indice(indice)
                            debenture.porcentagem = percentual_indice
        
                            if situacao == u'Excluído' and data_saida != '':
                                debenture.data_fim = datetime.datetime.strptime(data_saida, '%d/%m/%Y').date()
                            
                            debenture.save()
                                
                            if amortizacao_carencia or amortizacao_taxa > 0:
                                if not AmortizacaoDebenture.objects.filter(debenture=debenture, taxa=amortizacao_taxa, periodo=amortizacao_periodo, \
                                                                           unidade_periodo=amortizacao_unidade, tipo=amortizacao_tipo, carencia=amortizacao_carencia).exists():
                                    amortizacao = AmortizacaoDebenture(data = datetime.date.today(), debenture=debenture, taxa=amortizacao_taxa, \
                                                                       periodo=amortizacao_periodo, unidade_periodo=amortizacao_unidade, tipo=amortizacao_tipo, \
                                                                       carencia=amortizacao_carencia)
                                    amortizacao.save()
                            if juros_carencia:
                                if not JurosDebenture.objects.filter(debenture=debenture, taxa=juros_taxa, periodo=juros_periodo, \
                                                                     unidade_periodo=juros_unidade, carencia=juros_carencia).exists():
                                    juros = JurosDebenture(data = datetime.date.today(), debenture=debenture, taxa=juros_taxa, \
                                                                       periodo=juros_periodo, unidade_periodo=juros_unidade, carencia=juros_carencia)
                                    juros.save()
                            if premio_carencia:
                                if not PremioDebenture.objects.filter(debenture=debenture, taxa=premio_taxa, periodo=premio_periodo, \
                                                                      unidade_periodo=premio_unidade, carencia=premio_carencia).exists():
                                    premio = PremioDebenture(data = datetime.date.today(), debenture=debenture, taxa=premio_taxa, \
                                                                       periodo=premio_periodo, unidade_periodo=premio_unidade, carencia=premio_carencia)
                                    premio.save()
                        else:
                            # Data de emissão
                            data_emissao = datetime.datetime.strptime(campos[11], '%d/%m/%Y').date()
                            # Data de vencimento
                            data_vencimento = None if campos[12] == u'Indeterminado' else datetime.datetime.strptime(campos[12] , '%d/%m/%Y').date()
                            # Data de início de rendimento
                            data_inicio_rendimento = datetime.datetime.strptime(campos[15], '%d/%m/%Y').date()
                            # VNU de emissão
                            valor_nominal_emissao = campos[37]
                            # Índice
                            indice = campos[41]
                            if indice in [u'SELIC', u'PRÉ', u'IGP-M', u'IPCA', u'DI', u'PREFIXADO']:
                                # Alterar valor do índice para ser aceito nos tipos de indexação
                                if indice in [u'PRÉ',u'PREFIXADO']:
                                    indice = u'Prefixado'
                            else:
                                raise ValueError(u'Tipo não previsto: %s' % (campos[41]))
                            # Percentual multiplicador do índice
                            percentual_indice = Decimal(re.sub('[^\d,\.]', '', campos[47]).replace(',', '.') or '100')
                            # Situação
                            situacao = campos[5]
                            # Data último VNU
                            data_saida = campos[40]
                            # É debenture incentivada?
                            incentivada = campos[88]
                            
                            if Debenture.objects.filter(codigo=codigo).exists():
                                debenture = Debenture.objects.get(codigo=codigo)
                            else:
                                debenture = Debenture(codigo=codigo)
                                
                            debenture.data_emissao = data_emissao
                            debenture.valor_emissao = valor_nominal_emissao.replace('.', '').replace(',', '.')
                            debenture.data_inicio_rendimento = data_inicio_rendimento
                            debenture.data_vencimento = data_vencimento
                            debenture.incentivada = False if 'N' in incentivada.upper() else True
                            debenture.padrao_snd = False
                            debenture.indice = debenture.buscar_codigo_tipo_indice(indice)
                            debenture.porcentagem = percentual_indice
        
                            if situacao == u'Excluído' and data_saida != '':
                                debenture.data_fim = datetime.datetime.strptime(data_saida, '%d/%m/%Y').date()
                            
                            debenture.save()
                    except:
                        pass
                
                time.sleep(1)
        except Exception as e:
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(e).__name__, e.args)
            print codigo, 'processamento', message

class Command(BaseCommand):
    help = 'Busca as Debêntures'

    def handle(self, *args, **options):
        try:
            # Prepara thread de processamento de informações de debênture
            thread_processa_debenture = ProcessaDebentureThread()
            thread_processa_debenture.start()
            
            buscar_info_debentures()
            while (len(threads_rodando) > 0 or len(debentures_para_processar) > 0):
                if 'Principal' in threads_rodando.keys():
                    del threads_rodando['Principal']
                time.sleep(3)
        except KeyboardInterrupt:
            while (len(threads_rodando) > 0 or len(debentures_para_processar) > 0):
                print 'Debêntures a processar:', len(debentures_para_processar)
                if 'Principal' in threads_rodando.keys():
                    del threads_rodando['Principal']
                time.sleep(3)

def buscar_info_debentures():
    url_download_arquivo = 'http://www.debentures.com.br/exploreosnd/consultaadados/emissoesdedebentures/caracteristicas_e.asp?tip_deb=publicas&op_exc=Nada'
    req = Request(url_download_arquivo)
    try:
        response = urlopen(req)
    except HTTPError as e:
        print 'The server couldn\'t fulfill the request.'
        print 'Error code: ', e.code
    except URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
    else:
        data = response.read()
        print len(data)
        
        ler_debenture_prox_linha = False

        for linha in data.decode('latin-1').split('\n'):
            if u'Código do Ativo' in linha:
                ler_debenture_prox_linha = True
#                 for indice, campo in enumerate([campo.strip() for campo in linha.split('\t')]):
#                     print indice, campo
            elif ler_debenture_prox_linha:
                campos = [campo.strip() for campo in linha.split('\t')]
                
                if len(campos) > 1:
                    debentures_para_processar.append({campos[0]: campos})
