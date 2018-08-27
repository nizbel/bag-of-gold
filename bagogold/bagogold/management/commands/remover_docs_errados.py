# -*- coding: utf-8 -*-

from django.contrib.auth.models import Permission, User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models.aggregates import Sum
from django.db.models.query_utils import Q

from bagogold.bagogold.models.empresa import Empresa
from bagogold.bagogold.models.gerador_proventos import DocumentoProventoBovespa, \
    PendenciaDocumentoProvento, InvestidorRecusaDocumento, \
    InvestidorValidacaoDocumento, HistoricoInvestidorRecusaDocumento, \
    InvestidorLeituraDocumento, HistoricoInvestidorLeituraDocumento, \
    HistoricoInvestidorValidacaoDocumento, ProventoFIIDocumento
from bagogold.bagogold.utils.gerador_proventos import ler_provento_estruturado_fii, \
    reiniciar_documento
from bagogold.fii.models import ProventoFII


proventos_versionados = list()
documentos_validados_por_usuario = list()
documentos_com_recusa = list()

class Command(BaseCommand):
    help = 'Remove documentos errados'

    def handle(self, *args, **options):
        permissao = Permission.objects.get(codename='pode_gerar_proventos')  
        for usuario in User.objects.filter(Q(user_permissions=permissao) | Q(is_superuser=True)):
            print usuario.investidor, InvestidorLeituraDocumento.objects.filter(investidor=usuario.investidor).count()
            print usuario.investidor, InvestidorValidacaoDocumento.objects.filter(investidor=usuario.investidor).count()
        # Resultado
#         camilac3 1077
#         camilac3 1652
#         Elainej 2856
#         Elainej 0
#         nizbel 1639
#         nizbel 1469

        print 'Qtd historicos recusa', HistoricoInvestidorRecusaDocumento.objects.all().count()
        print 'Qtd historicos leitura', HistoricoInvestidorLeituraDocumento.objects.all().count()
        print 'Qtd leituras', InvestidorLeituraDocumento.objects.all().count()
        print 'Total leituras', InvestidorLeituraDocumento.objects.all().count() + HistoricoInvestidorLeituraDocumento.objects.all().count()
        print 'Qtd historicos validacao', HistoricoInvestidorValidacaoDocumento.objects.all().count()
        print 'Qtd validacoes', InvestidorValidacaoDocumento.objects.all().count()
        print 'Total validacoes', InvestidorValidacaoDocumento.objects.all().count() + HistoricoInvestidorValidacaoDocumento.objects.all().count()
        try:
            with transaction.atomic():
                docs_repetidos = {}
                docs = list(DocumentoProventoBovespa.objects.filter(tipo='F').order_by('protocolo'))
                for indice, doc in enumerate(docs):
                    for outro_doc in docs[indice+1:]:
                        if doc.protocolo == outro_doc.protocolo:
                            if doc.protocolo not in docs_repetidos.keys():
                                docs_repetidos[doc.protocolo] = [doc.id, outro_doc.id,]
                            elif outro_doc.id not in docs_repetidos[doc.protocolo]:
                                docs_repetidos[doc.protocolo].append(outro_doc.id)
                        elif doc.protocolo < outro_doc.protocolo:
                            break
         
                print len(docs_repetidos.keys())
                print sum([len(docs_repetidos[key]) for key in docs_repetidos])
                lista_prot_repetidos = docs_repetidos.keys()
        #         for key in docs_repetidos.keys():
        #             print key, '=>', docs_repetidos[key]
          
                print len(lista_prot_repetidos)
                
                # Deve haver 13146 repetidos
                docs_repetidos = DocumentoProventoBovespa.objects.filter(tipo='F', protocolo__in=lista_prot_repetidos).order_by('protocolo') # .filter(protocolo='27551')
                print docs_repetidos.count()
                
                for doc in docs_repetidos:
                    print doc
                    # Verificar se foi lido e validado pelo sistema
                    if not doc.pendente() and not InvestidorLeituraDocumento.objects.filter(documento=doc).exists() and not InvestidorValidacaoDocumento.objects.filter(documento=doc).exists():
                        # Verificar se empresa do provento é a mesma do documento
                        for provento_documento in ProventoFIIDocumento.objects.filter(documento=doc):
                            if doc.empresa != provento_documento.provento.fii.empresa:
                                print 'Empresa do documento e do provento nao batem', doc.empresa.ticker_empresa(), provento_documento.provento.fii.empresa.ticker_empresa()
                                
                                reiniciar_documento(doc)
                                break

#                 ler_provento_estruturado_fii(docs_repetidos.filter(protocolo='27551').get(empresa=Empresa.objects.get(codigo_cvm='ANCR')))
#                 ler_provento_estruturado_fii(docs_repetidos.filter(protocolo='27551').get(empresa=Empresa.objects.get(codigo_cvm='KNRE')))
                
                print '...'
        #         # Verificar quantidades de cada pendencia
        #         qtd_pendentes_leitura = 0
        #         qtd_pendentes_validacao = 0
        #         qtd_nao_pendentes = 0
        #         for doc in docs_repetidos:
        #             if doc.pendente():
        #                 if doc.pendencias()[0].tipo == PendenciaDocumentoProvento.TIPO_LEITURA:
        #                     qtd_pendentes_leitura += 1
        #                 elif doc.pendencias()[0].tipo == PendenciaDocumentoProvento.TIPO_VALIDACAO:
        #                     qtd_pendentes_validacao += 1
        #                 else:
        #                     raise ValueError('Pendência inválida')
        #             else:
        #                 qtd_nao_pendentes += 1
        #                 
        #         print qtd_pendentes_leitura, qtd_pendentes_validacao, qtd_nao_pendentes, qtd_pendentes_leitura + qtd_pendentes_validacao + qtd_nao_pendentes
                
                for doc in docs_repetidos:
                    print doc
                    # Apagar apenas documentos que possuam protocolo igual a um já validado
                    apagar_doc = verificar_se_existe_protocolo_validado(doc)
                    if apagar_doc:
                        if doc.pendente():
                            # Os que tem pendência de leitura: verificar se já foi recusado
                            if doc.pendencias()[0].tipo == PendenciaDocumentoProvento.TIPO_LEITURA:
                                # Se recusado, manter histórico de recusa
                                if InvestidorRecusaDocumento.objects.filter(documento=doc).exists():
                                    print 'Manter recusa'
                                    gerar_historico_recusas(doc)
                                # Se não, verificação para apagar
                                else:
                                    print 'Apenas apagar'
                    
                            # Pendencia de validação: manter recusas/leituras
                            elif doc.pendencias()[0].tipo == PendenciaDocumentoProvento.TIPO_VALIDACAO:
                                # Se recusado, manter histórico de recusa
                                if InvestidorRecusaDocumento.objects.filter(documento=doc).exists():
                                    print 'Manter recusa'
                                    gerar_historico_recusas(doc)
                                    
                                print 'Manter leitura'
                                gerar_historico_leitura(doc)
                            
                            else:
                                raise ValueError('Pendência inválida')
                        
                        else:
                            # Documentos validados
                            # Se recusado, manter histórico de recusa
                            if InvestidorRecusaDocumento.objects.filter(documento=doc).exists():
                                print 'Manter recusa'
                                gerar_historico_recusas(doc)
                                
                            print 'Manter leitura'
                            gerar_historico_leitura(doc)
                            
                            print 'Manter validação'
                            gerar_historico_validacao(doc)
                            
                        apagar_documento(doc)
                            
                print len(documentos_validados_por_usuario), 'documentos validados por usuario'
                print len(proventos_versionados), 'proventos versionados'
                print len(documentos_com_recusa), 'documentos com recusa'
        #         
        #         
        #         qtd_docs_repetidos = DocumentoProventoBovespa.objects.filter(tipo='F').values('protocolo').order_by('protocolo').annotate(qtd_docs=Count('protocolo')) \
        #             .filter(qtd_docs__gt=1)
        #         print qtd_docs_repetidos.count()
        #         print qtd_docs_repetidos.aggregate(total=Sum('qtd_docs'))
        
                print 'Qtd historicos recusa criados', HistoricoInvestidorRecusaDocumento.objects.all().count()
                print 'Qtd historicos leitura criados', HistoricoInvestidorLeituraDocumento.objects.all().count()
                print 'Qtd leituras', InvestidorLeituraDocumento.objects.all().count()
                print 'Total leituras', InvestidorLeituraDocumento.objects.all().count() + HistoricoInvestidorLeituraDocumento.objects.all().count()
                print 'Qtd historicos validacao criados', HistoricoInvestidorValidacaoDocumento.objects.all().count()
                print 'Qtd validacoes', InvestidorValidacaoDocumento.objects.all().count()
                print 'Total validacoes', InvestidorValidacaoDocumento.objects.all().count() + HistoricoInvestidorValidacaoDocumento.objects.all().count()
                
                # Verificar quantidade de docs repetidos
                docs_repetidos = {}
                docs = list(DocumentoProventoBovespa.objects.filter(tipo='F').order_by('protocolo'))
                for indice, doc in enumerate(docs):
                    for outro_doc in docs[indice+1:]:
                        if doc.protocolo == outro_doc.protocolo:
                            if doc.protocolo not in docs_repetidos.keys():
                                docs_repetidos[doc.protocolo] = [doc.id, outro_doc.id,]
                            elif outro_doc.id not in docs_repetidos[doc.protocolo]:
                                docs_repetidos[doc.protocolo].append(outro_doc.id)
                        elif doc.protocolo < outro_doc.protocolo:
                            break
         
                print len(docs_repetidos.keys())
                print sum([len(docs_repetidos[key]) for key in docs_repetidos])
                
                permissao = Permission.objects.get(codename='pode_gerar_proventos')  
                for usuario in User.objects.filter(Q(user_permissions=permissao) | Q(is_superuser=True)):
                    print usuario.investidor, InvestidorLeituraDocumento.objects.filter(investidor=usuario.investidor).count() \
                        + HistoricoInvestidorLeituraDocumento.objects.filter(investidor=usuario.investidor).count()
                    print usuario.investidor, InvestidorValidacaoDocumento.objects.filter(investidor=usuario.investidor).count() \
                        + HistoricoInvestidorValidacaoDocumento.objects.filter(investidor=usuario.investidor).count()
                # Resultado
#                 camilac3 1077
#                 camilac3 1652
#                 Elainej 2396
#                 Elainej 0
#                 nizbel 1639
#                 nizbel 1469

                for pendencia in PendenciaDocumentoProvento.objects.filter(documento__tipo_documento=DocumentoProventoBovespa.TIPO_DOCUMENTO_AVISO_COTISTAS_ESTRUTURADO,
                                                                   documento__tipo='F').order_by('documento__protocolo'):
                    try:
                        print 'ler', pendencia.documento
                        if not doc.verificar_arquivo_existe():
                            pendencia.documento.baixar_e_salvar_documento()
                        ler_provento_estruturado_fii(pendencia.documento)
                    except:
                        pass
                
                print 'Proventos criados:', HistoricoInvestidorLeituraDocumento.objects.all().aggregate(total_proventos=Sum('proventos_criados'))['total_proventos']
                
#                 raise ValueError('TESTE')
        except Exception as e:
            print 'ERRO:', e
#             raise
        print 'Qtd historicos recusa', HistoricoInvestidorRecusaDocumento.objects.all().count()
        print 'Qtd historicos leitura', HistoricoInvestidorLeituraDocumento.objects.all().count()
        print 'Qtd leituras', InvestidorLeituraDocumento.objects.all().count()
        print 'Total leituras', InvestidorLeituraDocumento.objects.all().count() + HistoricoInvestidorLeituraDocumento.objects.all().count()
        print 'Qtd historicos validacao', HistoricoInvestidorValidacaoDocumento.objects.all().count()
        print 'Qtd validacoes', InvestidorValidacaoDocumento.objects.all().count()
        print 'Total validacoes', InvestidorValidacaoDocumento.objects.all().count() + HistoricoInvestidorValidacaoDocumento.objects.all().count()
        
        
def verificar_se_existe_protocolo_validado(documento):
    """
    Verifica se já existe documento com o mesmo protocolo validado
    """
    docs_mesmo_protocolo = DocumentoProventoBovespa.objects.filter(tipo='F', protocolo=documento.protocolo).exclude(id=documento.id)
    
    existe_outro_doc_validado = False
    for doc in docs_mesmo_protocolo:
        if not doc.pendente():
            if InvestidorValidacaoDocumento.objects.filter(documento=doc).exists():
                print doc, 'já validado POR USUÁRIO'
                if doc not in documentos_validados_por_usuario:
                    documentos_validados_por_usuario.append(doc)
            else:
                print doc, 'já validado pelo sistema'
            
            # Verificar se provento mostrado bate com a empresa
            provento_empresa_correto = True
            for provento_documento in ProventoFIIDocumento.objects.filter(documento=doc):
                if doc.empresa == provento_documento.provento.fii.empresa:
                    print 'Empresa do documento e do provento batem', doc.empresa.ticker_empresa()
                    
                else:
                    provento_empresa_correto = False
                    print 'Documento', doc.empresa.ticker_empresa(), 'Provento', provento_documento.provento.fii.empresa.ticker_empresa()
                    
                if provento_documento.versao > 1:
                    if provento_documento not in proventos_versionados:
                        proventos_versionados.append(provento_documento)
                        
            if provento_empresa_correto:
                # Testar provento/empresa do documento de parametro
                if not documento.pendente():
                    for prov_doc_parametro in ProventoFIIDocumento.objects.filter(documento=documento):
                        print u'PARÂMETRO: Documento', documento.empresa.ticker_empresa(), 'Provento', prov_doc_parametro.provento.fii.empresa.ticker_empresa()
                        if documento.empresa != provento_documento.provento.fii.empresa:
                            existe_outro_doc_validado = True
                        else:
                            raise ValueError('Ambos documentos estão validados com proventos batendo')
                        
                    if not ProventoFIIDocumento.objects.filter(documento=documento).exists():
                        raise ValueError('Documento parâmetro validado e sem proventos')
                else:
                    existe_outro_doc_validado = True
            
            if existe_outro_doc_validado:
                break
            
    return existe_outro_doc_validado

def apagar_documento(documento):
    """
    Apaga documento mantendo histórico de leituras, recusas e validação
    """
    print 'Apagar', documento
    # Reiniciar documento para correções na descrição de provento relacionado
    reiniciar_documento(documento)
    documento.delete()

def gerar_historico_recusas(documento):
    """
    Gera histórico de recusas do documento a ser apagado
    """
    if InvestidorRecusaDocumento.objects.filter(documento=documento).exists():
        # Gerar todos os históricos de recusa
        for recusa in InvestidorRecusaDocumento.objects.filter(documento=documento):
            historico_recusa = HistoricoInvestidorRecusaDocumento(empresa=documento.empresa, protocolo=documento.protocolo,
                                                                  investidor=recusa.investidor, data_recusa=recusa.data_recusa,
                                                                  responsavel_leitura=recusa.responsavel_leitura,
                                                                  tipo_investimento=recusa.documento.tipo)
            print historico_recusa
            historico_recusa.save()

def gerar_historico_leitura(documento):
    """
    Gera histórico de leitura do documento a ser apagado
    """
    if InvestidorLeituraDocumento.objects.filter(documento=documento).exists():
        leitura = InvestidorLeituraDocumento.objects.get(documento=documento)
        # Gerar histórico de leitura
        historico_leitura = HistoricoInvestidorLeituraDocumento(empresa=documento.empresa, protocolo=documento.protocolo,
                                                                investidor=leitura.investidor, data_leitura=leitura.data_leitura,
                                                                decisao=leitura.decisao, tipo_investimento=leitura.documento.tipo,
                                                                proventos_criados=leitura.documento.proventofiidocumento_set.all().count())
        print historico_leitura
        historico_leitura.save()
        
#     else:
#         raise ValueError('Documento não possui leitura')
    
def gerar_historico_validacao(documento):
    """ 
    Gera histórico de validação do documento a ser apagado
    """
    if InvestidorValidacaoDocumento.objects.filter(documento=documento).exists():
        validacao = InvestidorValidacaoDocumento.objects.get(documento=documento)
        # Gerar histórico de validação
        historico_validacao = HistoricoInvestidorValidacaoDocumento(empresa=documento.empresa, protocolo=documento.protocolo,
                                                                investidor=validacao.investidor, data_validacao=validacao.data_validacao,
                                                                tipo_investimento=validacao.documento.tipo)
        print historico_validacao
        historico_validacao.save()
        
#     else:
#         raise ValueError('Documento não possui validação')