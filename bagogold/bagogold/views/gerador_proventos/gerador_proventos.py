# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal
import json
import os
import traceback

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required, \
    user_passes_test
from django.core.mail import mail_admins
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models.expressions import Case, When, Value
from django.db.models.fields import CharField
from django.forms.formsets import formset_factory
from django.forms.models import model_to_dict
from django.http.response import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.template.response import TemplateResponse

from bagogold import settings
from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.bagogold.forms.gerador_proventos import \
    ProventoAcaoDescritoDocumentoBovespaForm, \
    AcaoProventoAcaoDescritoDocumentoBovespaForm, \
    ProventoFIIDescritoDocumentoBovespaForm, SelicProventoAcaoDescritoDocBovespaForm
from bagogold.bagogold.models.acoes import Acao, Provento, AcaoProvento, \
    AtualizacaoSelicProvento, HistoricoAcao
from bagogold.bagogold.models.empresa import Empresa
from bagogold.bagogold.models.gerador_proventos import DocumentoProventoBovespa, \
    PendenciaDocumentoProvento, ProventoAcaoDescritoDocumentoBovespa, \
    ProventoAcaoDocumento, InvestidorResponsavelPendencia, \
    AcaoProventoAcaoDescritoDocumentoBovespa, ProventoFIIDocumento, \
    ProventoFIIDescritoDocumentoBovespa, SelicProventoAcaoDescritoDocBovespa
from bagogold.bagogold.utils.gerador_proventos import \
    alocar_pendencia_para_investidor, desalocar_pendencia_de_investidor, \
    salvar_investidor_responsavel_por_leitura, criar_descricoes_provento_acoes, \
    desfazer_investidor_responsavel_por_leitura, buscar_proventos_proximos_acao, \
    versionar_descricoes_relacionadas_acoes, \
    salvar_investidor_responsavel_por_validacao, \
    salvar_investidor_responsavel_por_recusar_documento, \
    criar_descricoes_provento_fiis, buscar_proventos_proximos_fii, \
    versionar_descricoes_relacionadas_fiis, relacionar_proventos_lidos_sistema, \
    reiniciar_documento
from bagogold.bagogold.utils.investidores import is_superuser
from bagogold.bagogold.utils.misc import \
    formatar_zeros_a_direita_apos_2_casas_decimais
from bagogold.fii.models import ProventoFII, FII


@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
def baixar_documento_provento(request, id_documento):
    if DocumentoProventoBovespa.objects.filter(id=id_documento).exists():
        documento_provento = DocumentoProventoBovespa.objects.get(id=id_documento)
        filename = documento_provento.documento.name.split('/')[-1]
        if documento_provento.extensao_documento() == 'doc':
            response = HttpResponse(documento_provento.documento, content_type='application/msword')
        elif documento_provento.extensao_documento() == 'xml':
            response = HttpResponse(documento_provento.documento, content_type='application/xml')
        else:
            response = HttpResponse(documento_provento.documento, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
        response['Content-Length'] = documento_provento.tamanho_arquivo()
    
        return response
    else:
        messages.error(request, 'Documento não foi encontrado para download')
        return HttpResponseRedirect(reverse('gerador_proventos:listar_pendencias'))

@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
@adiciona_titulo_descricao('Detalhar documento da Bovespa', 'Detalha informações de documento de proventos da Bovespa')
def detalhar_documento(request, id_documento):
    documento = DocumentoProventoBovespa.objects.filter(id=id_documento).prefetch_related('pendenciadocumentoprovento_set') \
        .select_related('investidorleituradocumento__investidor__user', 'investidorvalidacaodocumento__investidor__user')[0]
    documento.nome = documento.documento.name.split('/')[-1]
    
    # Se documento for ação
    if documento.tipo == 'A':
        proventos_descritos_ids = ProventoAcaoDocumento.objects.filter(documento=documento).values_list('descricao_provento_id', flat=True)
        proventos = ProventoAcaoDescritoDocumentoBovespa.objects.filter(id__in=proventos_descritos_ids)
        for provento in proventos:
            # Remover 0s a direita para valores
            provento.valor_unitario = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(provento.valor_unitario))
            if provento.tipo_provento == 'A':
                provento.acoes_recebidas = provento.acaoproventoacaodescritodocumentobovespa_set.all()
                # Remover 0s a direita para valores
                for acao_descricao_provento in provento.acoes_recebidas:
                    acao_descricao_provento.valor_calculo_frac = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(acao_descricao_provento.valor_calculo_frac))
            
            # Adicionar informação de versão
            provento.versao = provento.proventoacaodocumento.versao
    # Se for FII
    elif documento.tipo == 'F':
        proventos_descritos_ids = ProventoFIIDocumento.objects.filter(documento=documento).values_list('descricao_provento_id', flat=True)
        proventos = ProventoFIIDescritoDocumentoBovespa.objects.filter(id__in=proventos_descritos_ids)
        for provento in proventos:
            # Remover 0s a direita para valores
            provento.valor_unitario = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(provento.valor_unitario))
            # Adicionar informação de versão
            provento.versao = provento.proventofiidocumento.versao
        
    return TemplateResponse(request, 'gerador_proventos/detalhar_documento.html', {'documento': documento, 'proventos': proventos})

@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
@adiciona_titulo_descricao('Detalhar provento de uma Ação', 'Mostra valores e histórico de versionamento de um provento recebido por uma Ação')
def detalhar_provento_acao(request, id_provento):
    provento = Provento.gerador_objects.filter(id=id_provento).select_related('acao', 'atualizacaoselicprovento')[0]
    
    # Remover 0s a direita para valores
    provento.valor_unitario = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(provento.valor_unitario))
    if provento.tipo_provento == 'A':
        provento.acoes_recebidas = provento.acaoprovento_set.all()
        # Remover 0s a direita para valores
        for acao_descricao_provento in provento.acoes_recebidas:
            acao_descricao_provento.valor_calculo_frac = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(acao_descricao_provento.valor_calculo_frac))

    # Adicionar informação de versão
    try:
        provento.versao = ProventoAcaoDocumento.objects.filter(provento=provento).order_by('-versao')[0].versao
        versoes = ProventoAcaoDescritoDocumentoBovespa.objects.filter(proventoacaodocumento__provento=provento).order_by('proventoacaodocumento__versao') \
            .select_related('acao', 'proventoacaodocumento__documento', 'selicproventoacaodescritodocbovespa')
        for versao in versoes:
            # Remover 0s a direita para valores
            versao.valor_unitario = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(versao.valor_unitario))
            if versao.tipo_provento == 'A':
                versao.acoes_recebidas = versao.acaoproventoacaodescritodocumentobovespa_set.all()
                # Remover 0s a direita para valores
                for acao_descricao_provento in versao.acoes_recebidas:
                    acao_descricao_provento.valor_calculo_frac = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(acao_descricao_provento.valor_calculo_frac))
    except Exception as e:
        provento.versao = 0
        versoes = list()
#         print e
    
    return TemplateResponse(request, 'gerador_proventos/detalhar_provento_acao.html', {'provento': provento, 'versoes': versoes})

@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
@adiciona_titulo_descricao('Detalhar provento de um FII', 'Mostra valores e histórico de versionamento de um provento recebido por um Fundo de Investimento Imobiliário')
def detalhar_provento_fii(request, id_provento):
    provento = ProventoFII.gerador_objects.get(id=id_provento)
    
    # Verifica se requisição é ajax, para o relacionamento entre proventos
    if request.is_ajax() and request.user.is_superuser:
        proventos_relacionaveis = buscar_proventos_proximos_fii(list(provento.proventofiidocumento_set.all())[-1].descricao_provento)

        return HttpResponse(json.dumps(render_to_string('gerador_proventos/utils/relacionar_proventos_fii.html', {'proventos_relacionaveis': proventos_relacionaveis,
                                                                                                                  'provento': provento})), content_type = "application/json")  
        
    # Remover 0s a direita para valores
    provento.valor_unitario = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(provento.valor_unitario))
    
    # Adicionar informação de versão
    try:
        provento.versao = ProventoFIIDocumento.objects.filter(provento=provento).order_by('-versao')[0].versao
        versoes = ProventoFIIDescritoDocumentoBovespa.objects.filter(proventofiidocumento__provento=provento).order_by('proventofiidocumento__versao')
        for versao in versoes:
            # Remover 0s a direita para valores
            versao.valor_unitario = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(versao.valor_unitario))
    except Exception as e:
        provento.versao = 0
        versoes = list()

    return TemplateResponse(request, 'gerador_proventos/detalhar_provento_fii.html', {'provento': provento, 'versoes': versoes})

@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
@adiciona_titulo_descricao('Ler documento da Bovespa', 'Ler documento da Bovespa e determinar se descreve recebimento de proventos ou não')
def ler_documento_provento(request, id_pendencia):
    # Usado para criar objetos vazios
    class Object(object):
        pass
    
    try:
        pendencia = PendenciaDocumentoProvento.objects.select_related('documento', 'documento__empresa').get(id=id_pendencia)
        # Verificar se pendência é de leitura
        if pendencia.tipo != 'L':
            messages.success(request, 'Pendência não é de leitura')
            return HttpResponseRedirect(reverse('gerador_proventos:listar_pendencias'))
    except PendenciaDocumentoProvento.DoesNotExist:
        messages.error(request, 'Pendência de leitura não foi encontrada')
        return HttpResponseRedirect(reverse('gerador_proventos:listar_pendencias'))
        
    investidor = request.user.investidor
    
    # Verifica se pendência já possui proventos descritos (foi feita recusa)
    # Para ações
    if pendencia.documento.tipo == 'A':
        form_extra = 0 if ProventoAcaoDocumento.objects.filter(documento=pendencia.documento).exists() else 1
        ProventoFormset = formset_factory(ProventoAcaoDescritoDocumentoBovespaForm, extra=form_extra)
        AcaoProventoFormset = formset_factory(AcaoProventoAcaoDescritoDocumentoBovespaForm, extra=form_extra)
        SelicProventoAcaoDescritoDocBovespaFormset = formset_factory(SelicProventoAcaoDescritoDocBovespaForm, extra=form_extra)
    # Para FIIs
    elif pendencia.documento.tipo == 'F':
        form_extra = 0 if ProventoFIIDocumento.objects.filter(documento=pendencia.documento).exists() else 1
        ProventoFormset = formset_factory(ProventoFIIDescritoDocumentoBovespaForm, extra=form_extra)
    
    if request.method == 'POST':
        # Verifica se pendência não possuia responsável e usuário acaba de reservá-la
        if request.POST.get('reservar'):
            # Verifica se a reserva está sendo feita ou cancelada
            if request.POST.get('reservar') == '1':
                # Calcular quantidade de pendências reservadas
                qtd_pendencias_reservadas = InvestidorResponsavelPendencia.objects.filter(investidor=investidor).count()
                if qtd_pendencias_reservadas == PendenciaDocumentoProvento.MAX_PENDENCIAS_POR_USUARIO:
                    messages.error(request, u'Você já possui %s pendências reservadas' % (PendenciaDocumentoProvento.MAX_PENDENCIAS_POR_USUARIO))
                else:
                    # Tentar alocar para o usuário
                    retorno, mensagem = alocar_pendencia_para_investidor(pendencia, investidor)
                    
                    if retorno:
                        # Atualizar pendência
                        pendencia = PendenciaDocumentoProvento.objects.get(id=id_pendencia)
                        messages.success(request, mensagem)
                    else:
                        messages.error(request, mensagem)
                        
            # Cancelar 
            elif request.POST.get('reservar') == '2':
                retorno, mensagem = desalocar_pendencia_de_investidor(pendencia, investidor)
                if retorno:
                    # Atualizar pendência
                    pendencia = PendenciaDocumentoProvento.objects.get(id=id_pendencia)
                    messages.success(request, mensagem)
                else:
                    messages.error(request, mensagem)
                
            # Preparar formset de proventos
            if pendencia.documento.tipo == 'A':
                formset_provento = ProventoFormset(prefix='provento')
                formset_acao_provento = AcaoProventoFormset(prefix='acao_provento')
                formset_acao_selic = SelicProventoAcaoDescritoDocBovespaFormset(prefix='acao_selic')
            elif pendencia.documento.tipo == 'F':
                formset_provento = ProventoFormset(prefix='provento')
                formset_acao_provento = {}
                formset_acao_selic = {}
                    
        elif request.POST.get('preparar_proventos'):
            if request.POST['num_proventos'].isdigit():
                qtd_proventos = int(request.POST['num_proventos']) if request.POST['num_proventos'] in [str(valor) for valor in range(0, 31)] else 1
                # Ações
                if pendencia.documento.tipo == 'A':
                    # Testa se quantidade de proventos engloba todos os proventos já cadastrados
                    if qtd_proventos >= ProventoAcaoDocumento.objects.filter(documento=pendencia.documento).count():
                        qtd_proventos_extra = qtd_proventos - ProventoAcaoDocumento.objects.filter(documento=pendencia.documento).count()
                    else:
                        qtd_proventos_extra = 0
                    ProventoFormset = formset_factory(ProventoAcaoDescritoDocumentoBovespaForm, extra=qtd_proventos_extra)
                    AcaoProventoFormset = formset_factory(AcaoProventoAcaoDescritoDocumentoBovespaForm, extra=qtd_proventos_extra)
                    SelicProventoAcaoDescritoDocBovespaFormset = formset_factory(SelicProventoAcaoDescritoDocBovespaForm, extra=qtd_proventos_extra)
    
                    # Proventos
                    proventos_iniciais = list()
                    # Limita a quantidade de proventos a mostrar dependendo da quantidade de proventos escolhida no formulario
                    for provento_acao_documento in pendencia.documento.proventoacaodocumento_set.all()[:min(qtd_proventos, pendencia.documento.proventoacaodocumento_set.count())]:
                        proventos_iniciais.append(model_to_dict(provento_acao_documento.descricao_provento))
                    formset_provento = ProventoFormset(prefix='provento', initial=proventos_iniciais)
                    # Ações de proventos
                    acoes_provento_iniciais = list()
                    for provento in proventos_iniciais:
                        if AcaoProventoAcaoDescritoDocumentoBovespa.objects.filter(provento__id=provento['id']).exists():
                            acoes_provento_iniciais.append(model_to_dict(AcaoProventoAcaoDescritoDocumentoBovespa.objects.get(provento__id=provento['id'])))
                        else:
                            acoes_provento_iniciais.append({})
                    formset_acao_provento = AcaoProventoFormset(prefix='acao_provento', initial=acoes_provento_iniciais)
                    
                    # Atualizações de proventos pela Selic
                    acoes_selic_iniciais = list()
                    for provento in proventos_iniciais:
                        if SelicProventoAcaoDescritoDocBovespa.objects.filter(provento__id=provento['id']).exists():
                            acoes_selic_iniciais.append(model_to_dict(SelicProventoAcaoDescritoDocBovespa.objects.get(provento__id=provento['id'])))
                        else:
                            acoes_selic_iniciais.append({})
                    formset_acao_selic = SelicProventoAcaoDescritoDocBovespaFormset(prefix='acao_selic', initial=acoes_selic_iniciais)
                # FII
                elif pendencia.documento.tipo == 'F':
                    # Testa se quantidade de proventos engloba todos os proventos já cadastrados
                    if qtd_proventos >= ProventoFIIDocumento.objects.filter(documento=pendencia.documento).count():
                        qtd_proventos_extra = qtd_proventos - ProventoFIIDocumento.objects.filter(documento=pendencia.documento).count()
                    else:
                        qtd_proventos_extra = 0
                    ProventoFormset = formset_factory(ProventoFIIDescritoDocumentoBovespaForm, extra=qtd_proventos_extra)
    
                    # Proventos
                    proventos_iniciais = list()
                    # Limita a quantidade de proventos a mostrar dependendo da quantidade de proventos escolhida no formulario
                    for provento_fii_documento in pendencia.documento.proventoacaodocumento_set.all()[:min(qtd_proventos, pendencia.documento.proventoacaodocumento_set.count())]:
                        proventos_iniciais.append(model_to_dict(provento_fii_documento.descricao_provento))
                    formset_provento = ProventoFormset(prefix='provento', initial=proventos_iniciais)
                    formset_acao_provento = {}
                    formset_acao_selic = {}
                    
                
        # Caso o botão de salvar ter sido apertado
        elif request.POST.get('save'):
            # Radio de documento estava em Gerar
            if request.POST['radioDocumento'] == '1':
#                 print request.POST
                if pendencia.documento.tipo == 'A':
                    formset_provento = ProventoFormset(request.POST, prefix='provento')
                    formset_acao_provento = AcaoProventoFormset(request.POST, prefix='acao_provento')
                    formset_acao_selic = SelicProventoAcaoDescritoDocBovespaFormset(request.POST, prefix='acao_selic')
                    
                    # Apaga descrições que já existam para poder rodar validações, serão posteriormente readicionadas caso haja algum erro
                    info_proventos_a_apagar = list(ProventoAcaoDocumento.objects.filter(documento=pendencia.documento)) \
                        + list(AcaoProvento.objects.filter(provento__id__in=ProventoAcaoDocumento.objects.filter(documento=pendencia.documento).values_list('provento', flat=True))) \
                        + list(AtualizacaoSelicProvento.objects.filter(provento__id__in=ProventoAcaoDocumento.objects.filter(documento=pendencia.documento).values_list('provento', flat=True))) \
                        + list(Provento.gerador_objects.filter(id__in=ProventoAcaoDocumento.objects.filter(documento=pendencia.documento).values_list('provento', flat=True))) \
                        + list(AcaoProventoAcaoDescritoDocumentoBovespa.objects.filter(provento__id__in=ProventoAcaoDocumento.objects.filter(documento=pendencia.documento).values_list('descricao_provento', flat=True))) \
                        + list(SelicProventoAcaoDescritoDocBovespa.objects.filter(provento__id__in=ProventoAcaoDocumento.objects.filter(documento=pendencia.documento).values_list('descricao_provento', flat=True))) \
                        + list(ProventoAcaoDescritoDocumentoBovespa.objects.filter(id__in=ProventoAcaoDocumento.objects.filter(documento=pendencia.documento).values_list('descricao_provento', flat=True)))
    #                 print info_proventos_a_apagar
    #                 print list(reversed(info_proventos_a_apagar))
                    for elemento in info_proventos_a_apagar:
                        # Mantém os IDs dos elementos
                        elemento.guarda_id = elemento.id
                        elemento.delete()
                        elemento.id = elemento.guarda_id
                    
                    if formset_provento.is_valid():
                        # Verifica se dados inseridos são todos válidos
                        forms_validos = True
                        indice_provento = 0
                        # Guarda os proventos, ações de proventos e atualizações pela Selic criadas 
                        # para salvar caso todos os formulários sejam válidos
                        proventos_validos = list()
                        acoes_proventos_validos = list()
                        acoes_selic_validos = list()
                        for form_provento in formset_provento:
                            provento = form_provento.save(commit=False)
    #                         print provento
                            proventos_validos.append(provento)
                            form_acao_provento = formset_acao_provento[indice_provento]
                            form_acao_selic = formset_acao_selic[indice_provento]
                            # Verificar a ação do provento em ações
                            if provento.tipo_provento == 'A':
                                acao_provento = form_acao_provento.save(commit=False) if form_acao_provento.is_valid() \
                                    and form_acao_provento.has_changed() else None
                                if acao_provento == None:
                                    forms_validos = False
                                else:
                                    acao_provento.provento = provento
    #                                 print acao_provento
                                    acoes_proventos_validos.append(acao_provento)
                            
                            # Se provento não é em ações, pode ser atualizado pela Selic
                            else:
                                acao_selic = form_acao_selic.save(commit=False) if form_acao_selic.is_valid() \
                                    and form_acao_selic.has_changed() else None
                                if acao_selic != None:
                                    acao_selic.provento = provento
                                    acoes_selic_validos.append(acao_selic)
                            indice_provento += 1
                            
                        if forms_validos:
                            try:
                                # Colocar investidor como responsável pela leitura do documento
                                salvar_investidor_responsavel_por_leitura(pendencia, investidor, decisao='C')
                                # Salvar descrições de proventos
                                criar_descricoes_provento_acoes(proventos_validos, acoes_proventos_validos, acoes_selic_validos, pendencia.documento)
                                messages.success(request, 'Descrições de proventos criadas com sucesso')
                                return HttpResponseRedirect(reverse('gerador_proventos:listar_pendencias'))
                            except Exception as e:
                                desfazer_investidor_responsavel_por_leitura(pendencia, investidor)
                                messages.error(request, str(e))
                        else:
                            messages.error(request, 'Proventos em ações não conferem com os proventos criados')
                    
                    # Readiciona proventos para o caso de não haver logrado sucesso na leitura
                    for elemento in list(reversed(info_proventos_a_apagar)):
                        elemento.save()
                    
                    # Testando erros
#                     print formset_provento.errors, formset_provento.non_form_errors()
                    for form in formset_provento:
                        for erro in form.non_field_errors():
                            messages.error(request, erro)
                elif pendencia.documento.tipo == 'F':
                    formset_provento = ProventoFormset(request.POST, prefix='provento')
                    formset_acao_provento = {}
                    formset_acao_selic = {}
                    
                    # Apaga descrições que já existam para poder rodar validações, serão posteriormente readicionadas caso haja algum erro
                    info_proventos_a_apagar = list(ProventoFIIDocumento.objects.filter(documento=pendencia.documento)) \
                        + list(ProventoFII.gerador_objects.filter(id__in=ProventoFIIDocumento.objects.filter(documento=pendencia.documento).values_list('provento', flat=True))) \
                        + list(ProventoFIIDescritoDocumentoBovespa.objects.filter(id__in=ProventoFIIDocumento.objects.filter(documento=pendencia.documento).values_list('descricao_provento', flat=True)))
    #                 print info_proventos_a_apagar
    #                 print list(reversed(info_proventos_a_apagar))
                    for elemento in info_proventos_a_apagar:
                        # Mantém os IDs dos elementos
                        elemento.guarda_id = elemento.id
                        elemento.delete()
                        elemento.id = elemento.guarda_id
                    
                    if formset_provento.is_valid():
                        # Verifica se dados inseridos são todos válidos
                        indice_provento = 0
                        # Guarda os proventos e ações de proventos criadas para salvar caso todos os formulários sejam válidos
                        proventos_validos = list()
                        acoes_proventos_validos = list()
                        for form_provento in formset_provento:
                            provento = form_provento.save(commit=False)
    #                         print provento
                            proventos_validos.append(provento)
                            indice_provento += 1
                        try:
                            # Colocar investidor como responsável pela leitura do documento
                            salvar_investidor_responsavel_por_leitura(pendencia, investidor, decisao='C')
                            # Salvar descrições de proventos
                            criar_descricoes_provento_fiis(proventos_validos, pendencia.documento)
                            messages.success(request, 'Descrições de proventos criadas com sucesso')
                            return HttpResponseRedirect(reverse('gerador_proventos:listar_pendencias'))
                        except Exception as e:
                            desfazer_investidor_responsavel_por_leitura(pendencia, investidor)
                            messages.error(request, str(e))
                    
                    # Readiciona proventos para o caso de não haver logrado sucesso na leitura
                    for elemento in list(reversed(info_proventos_a_apagar)):
                        elemento.save()
                    
                    # Testando erros
#                     print formset_provento.errors, formset_provento.non_form_errors()
                    for form in formset_provento:
                        for erro in form.non_field_errors():
                            messages.error(request, erro)
                
            # Radio de documento estava em Excluir
            elif request.POST['radioDocumento'] == '0':
                try:
                    with transaction.atomic():
                        # Preparar elementos a apagar
                        if pendencia.documento.tipo == 'A':
                            info_proventos_a_apagar = list(ProventoAcaoDocumento.objects.filter(documento=pendencia.documento)) \
                                + list(AcaoProvento.objects.filter(provento__id__in=ProventoAcaoDocumento.objects.filter(documento=pendencia.documento).values_list('provento', flat=True))) \
                                + list(AtualizacaoSelicProvento.objects.filter(provento__id__in=ProventoAcaoDocumento.objects.filter(documento=pendencia.documento).values_list('provento', flat=True))) \
                                + list(Provento.gerador_objects.filter(id__in=ProventoAcaoDocumento.objects.filter(documento=pendencia.documento).values_list('provento', flat=True))) \
                                + list(AcaoProventoAcaoDescritoDocumentoBovespa.objects.filter(provento__id__in=ProventoAcaoDocumento.objects.filter(documento=pendencia.documento).values_list('descricao_provento', flat=True))) \
                                + list(SelicProventoAcaoDescritoDocBovespa.objects.filter(provento__id__in=ProventoAcaoDocumento.objects.filter(documento=pendencia.documento).values_list('descricao_provento', flat=True))) \
                                + list(ProventoAcaoDescritoDocumentoBovespa.objects.filter(id__in=ProventoAcaoDocumento.objects.filter(documento=pendencia.documento).values_list('descricao_provento', flat=True)))
                        elif pendencia.documento.tipo == 'F':
                            info_proventos_a_apagar = list(ProventoFIIDocumento.objects.filter(documento=pendencia.documento)) \
                                + list(ProventoFII.gerador_objects.filter(id__in=ProventoFIIDocumento.objects.filter(documento=pendencia.documento).values_list('provento', flat=True))) \
                                + list(ProventoFIIDescritoDocumentoBovespa.objects.filter(id__in=ProventoFIIDocumento.objects.filter(documento=pendencia.documento).values_list('descricao_provento', flat=True)))
                        for elemento in info_proventos_a_apagar:
                            elemento.delete()
                        
                        # Colocar investidor como responsável pela leitura do documento
                        salvar_investidor_responsavel_por_leitura(pendencia, investidor, decisao='E')
                        messages.success(request, 'Exclusão de arquivo registrada com sucesso')
                        return HttpResponseRedirect(reverse('gerador_proventos:listar_pendencias'))
                except Exception as e:
                    messages.error(request, str(e))
    else:
        # Preparar formset de proventos
        if pendencia.documento.tipo == 'A':
            # Proventos
            proventos_iniciais = list()
            for provento_acao_documento in pendencia.documento.proventoacaodocumento_set.all():
                proventos_iniciais.append(model_to_dict(provento_acao_documento.descricao_provento))
            formset_provento = ProventoFormset(prefix='provento', initial=proventos_iniciais)
            # Ações de proventos
            acoes_provento_iniciais = list()
            for provento in proventos_iniciais:
                if AcaoProventoAcaoDescritoDocumentoBovespa.objects.filter(provento__id=provento['id']).exists():
                    acoes_provento_iniciais.append(model_to_dict(AcaoProventoAcaoDescritoDocumentoBovespa.objects.get(provento__id=provento['id'])))
                else:
                    acoes_provento_iniciais.append({})
            formset_acao_provento = AcaoProventoFormset(prefix='acao_provento', initial=acoes_provento_iniciais)
    
            # Atualizações de proventos pela Selic
            acoes_selic_iniciais = list()
            for provento in proventos_iniciais:
                if SelicProventoAcaoDescritoDocBovespa.objects.filter(provento__id=provento['id']).exists():
                    acoes_selic_iniciais.append(model_to_dict(SelicProventoAcaoDescritoDocBovespa.objects.get(provento__id=provento['id'])))
                else:
                    acoes_selic_iniciais.append({})
            formset_acao_selic = SelicProventoAcaoDescritoDocBovespaFormset(prefix='acao_selic', initial=acoes_selic_iniciais)
        
        elif pendencia.documento.tipo == 'F':
            # Proventos de FII
            proventos_iniciais = list()
            for provento_fii_documento in pendencia.documento.proventofiidocumento_set.all():
                proventos_iniciais.append(model_to_dict(provento_fii_documento.descricao_provento))
            formset_provento = ProventoFormset(prefix='provento', initial=proventos_iniciais)
            formset_acao_provento = {}
            formset_acao_selic = {}
            
    # Preparar opções de busca, tanto para POST quanto para GET
    if pendencia.documento.tipo == 'A':
        for form in formset_provento:
            form.fields['acao'].queryset = Acao.objects.filter(empresa=pendencia.documento.empresa)
            
        # Preparar informações sobre negociação das ações que são mostradas como opção
        infos_uteis = {'historico_negociacao': list()}
        for acao in Acao.objects.filter(empresa=pendencia.documento.empresa):
            try:
                negociacao_acao = Object()
                negociacao_acao.ticker = acao.ticker
                negociacao_acao.inicio = HistoricoAcao.objects.filter(oficial_bovespa=True, acao=acao).order_by('data')[0].data
                negociacao_acao.fim = HistoricoAcao.objects.filter(oficial_bovespa=True, acao=acao).order_by('-data')[0].data
                infos_uteis['historico_negociacao'].append(negociacao_acao)
            except:
                pass
        
        # Se histórico de negociação estiver vazio, removê-lo
        if len(infos_uteis['historico_negociacao']) == 0:
            del infos_uteis['historico_negociacao']
    elif pendencia.documento.tipo == 'F':
        for form in formset_provento:
            form.fields['fii'].queryset = FII.objects.filter(empresa=pendencia.documento.empresa)
        
        infos_uteis = {}
    # Preparar motivo de recusa, caso haja
    recusa = pendencia.documento.ultima_recusa()
    
    return TemplateResponse(request, 'gerador_proventos/ler_documento_provento.html', {'pendencia': pendencia, 'formset_provento': formset_provento, 'formset_acao_provento': formset_acao_provento, \
                                                                                       'formset_acao_selic': formset_acao_selic, 'recusa': recusa, 'infos_uteis': infos_uteis})
    
@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
@adiciona_titulo_descricao('Listar documentos da Bovespa', 'Listar documentos da Bovespa baixados pelo sistema')
def listar_documentos(request):
    # Verifica se existe empresa
    if not Empresa.objects.exists():
        return TemplateResponse(request, 'gerador_proventos/listar_documentos.html', {'documentos': list(), 'empresas': list(), 'empresa_atual': None})
    
    # Mostrar empresa atual
    if request.method == 'POST' and request.POST.get("busca_empresa"):
        empresa_atual = Empresa.objects.get(id=request.POST['busca_empresa'].replace('.', ''))
    else:
        empresa_atual = Empresa.objects.all().order_by('id')[0]
    
    empresas = Empresa.objects.all().order_by('nome')

    documentos = DocumentoProventoBovespa.objects.filter(empresa__id=empresa_atual.id).annotate(tipo_investimento=Case(When(tipo='A', then=Value(u'Ação')),
                                When(tipo='F', then=Value('FII')), output_field=CharField())) \
        .select_related('empresa').order_by('data_referencia')
    
    # Preencher pendências e proventos vinculados    
    pendencias = PendenciaDocumentoProvento.objects.filter(documento__id__in=[documento.id for documento in documentos]) \
        .order_by('documento').values_list('documento', flat=True).distinct()
        
    proventos_vinculados = list(ProventoAcaoDocumento.objects.filter(documento__id__in=[documento.id for documento in documentos]) \
        .order_by('documento').values_list('documento', flat=True).distinct())
    proventos_vinculados.extend(list(ProventoFIIDocumento.objects.filter(documento__id__in=[documento.id for documento in documentos]) \
        .order_by('documento').values_list('documento', flat=True).distinct()))
    
    # Buscar ticker de ações para preencher ticker de empresa
    ticker_acoes = Acao.objects.all().order_by('empresa').values('empresa').values_list('empresa', 'ticker')
    
    # Preencher ticker de empresa para lista de empresas
    for empresa in empresas:
        if empresa.codigo_cvm == None or any([char.isdigit() for char in empresa.codigo_cvm]):
            for empresa_id, ticker in ticker_acoes:
                if empresa.id == empresa_id:
                    empresa.ticker_empresa = ticker
                    break
        else:
            empresa.ticker_empresa = empresa.codigo_cvm
            
    # Preencher ticker de empresa para empresa atual
    if empresa_atual.codigo_cvm == None or any([char.isdigit() for char in empresa_atual.codigo_cvm]):
        for empresa_id, ticker in ticker_acoes:
            if empresa_atual.id == empresa_id:
                empresa_atual.ticker_empresa = ticker
                break
    else:
        empresa_atual.ticker_empresa = empresa_atual.codigo_cvm
            
    
    for documento in documentos:
        documento.ha_proventos_vinculados = documento.id in proventos_vinculados
        
        documento.pendente = documento.id in pendencias
        
        # Preencher ticker de empresa
        if documento.empresa.codigo_cvm == None or any([char.isdigit() for char in documento.empresa.codigo_cvm]):
            for empresa_id, ticker in ticker_acoes:
                if documento.empresa.id == empresa_id:
                    documento.nome = u'%s-%s' % (''.join(char for char in ticker if not char.isdigit()), documento.protocolo)
                    break
        else:
            documento.nome = u'%s-%s' % (documento.empresa.codigo_cvm, documento.protocolo)
            
    return TemplateResponse(request, 'gerador_proventos/listar_documentos.html', {'documentos': documentos, 'empresas': empresas, 'empresa_atual': empresa_atual})


@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
@adiciona_titulo_descricao('Listar pendências', 'Listagem de pendências de leitura/validação em documentos da Bovespa')
def listar_pendencias(request):
    # Usado para criar objetos vazios
    class Object(object):
        pass
    
    investidor = request.user.investidor
    
    # Valor padrão para o filtro de quantidade
    filtros = Object()
    # Prepara a busca
    query_pendencias = PendenciaDocumentoProvento.objects.all().annotate(tipo_pendencia=Case(When(tipo='L', then=Value(u'Leitura')), 
                                                                                             When(tipo='V', then=Value(u'Validação')), output_field=CharField())) \
        .annotate(tipo_documento=Case(When(documento__tipo='A', then=Value(u'Ação')), When(documento__tipo='F', then=Value('FII')), output_field=CharField())) \
        .select_related('documento__empresa', 'investidorresponsavelpendencia__investidor__user')
    # Verifica a quantidade de pendências escolhida para filtrar
    if request.method == 'POST':
        # Preparar filtro por quantidade
        if request.POST.get("filtro_qtd") and request.POST.get('filtro_qtd').isdigit():
            filtros.filtro_qtd = int(request.POST['filtro_qtd'])
        # Preparar filtro por tipo de pendência
        filtros.filtro_tipo_leitura = 'filtro_tipo_leitura' in request.POST
        filtros.filtro_tipo_validacao = 'filtro_tipo_validacao' in request.POST
        # Preparar filtro por pendências reserváveis
        filtros.filtro_reservaveis = 'filtro_reservaveis' in request.POST
        # Preparar filtro para tipo de investimento
        filtros.filtro_tipo_inv = request.POST.get('filtro_tipo_inv')
    else:
        filtros.filtro_qtd = 200
        filtros.filtro_tipo_leitura = True
        filtros.filtro_tipo_validacao = True
        filtros.filtro_reservaveis = True
        # Valores são F (FII), A (Ação) e T (Todos)
        filtros.filtro_tipo_inv = 'T'
        
    # Filtrar
    if filtros.filtro_tipo_inv == 'A':
        query_pendencias = query_pendencias.filter(documento__tipo='A')
    elif filtros.filtro_tipo_inv == 'F':
        query_pendencias = query_pendencias.filter(documento__tipo='F')
        
    if not filtros.filtro_tipo_leitura:
        query_pendencias = query_pendencias.exclude(tipo='L')
    if not filtros.filtro_tipo_validacao:
        query_pendencias = query_pendencias.exclude(tipo='V')
    if filtros.filtro_reservaveis:
        query_pendencias = query_pendencias.exclude(tipo='V', documento__investidorleituradocumento__investidor=investidor)
        query_pendencias = query_pendencias.filter(investidorresponsavelpendencia=None)
    
    if PendenciaDocumentoProvento.objects.all().count() <= filtros.filtro_qtd:
        pendencias = query_pendencias
    else:
        pendencias = query_pendencias[:filtros.filtro_qtd]
    
    
    # Calcular quantidade de pendências reservadas
    qtd_pendencias_reservadas = InvestidorResponsavelPendencia.objects.filter(investidor=investidor).count()
    
    # Buscar ticker de ações para preencher ticker de empresa
    ticker_acoes = Acao.objects.all().order_by('empresa').values('empresa').values_list('empresa', 'ticker')
    
    for pendencia in pendencias:
#         pendencia.nome = pendencia.documento.documento.name.split('/')[-1]
#         pendencia.tipo_documento = 'Ação' if pendencia.documento.tipo == 'A' else 'FII'
#         pendencia.tipo_pendencia = 'Leitura' if pendencia.tipo == 'L' else 'Validação'
        pendencia.responsavel = pendencia.responsavel()
        
        # Preencher ticker de empresa
        if pendencia.documento.empresa.codigo_cvm == None or any([char.isdigit() for char in pendencia.documento.empresa.codigo_cvm]):
            for empresa_id, ticker in ticker_acoes:
                if pendencia.documento.empresa.id == empresa_id:
                    pendencia.documento.nome = u'%s-%s' % (''.join(char for char in ticker if not char.isdigit()), pendencia.documento.protocolo)
                    break
        else:
            pendencia.documento.nome = u'%s-%s' % (pendencia.documento.empresa.codigo_cvm, pendencia.documento.protocolo)
        
    return TemplateResponse(request, 'gerador_proventos/listar_pendencias.html', {'pendencias_doc_bovespa': pendencias, 'qtd_pendencias_reservadas': qtd_pendencias_reservadas,'filtros': filtros})


@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
@adiciona_titulo_descricao('Listagem de proventos de Ações e FIIs', 'Listar proventos recebidos por Ações e FIIs cadastrados no sistema')
def listar_proventos(request):
    # Usado para criar objetos vazios
    class Object(object):
        pass
    
    # Valor padrão para o filtro de quantidade
    filtros = Object()
    # Verifica a quantidade de pendências escolhida para filtrar
    if request.method == 'POST':
        # Preparar filtro por tipo de investimento
        filtros.filtro_investimento = request.POST.get('filtro_investimento')
        if filtros.filtro_investimento == 'A':
            query_proventos = Provento.gerador_objects.all()
        elif filtros.filtro_investimento == 'F':
            query_proventos = ProventoFII.gerador_objects.all()
        else:
            query_proventos = []
            
        # Preparar filtro para apenas documentos validados
        filtros.filtro_validados = 'filtro_validados' in request.POST
        if filtros.filtro_validados:
            query_proventos = query_proventos.filter(oficial_bovespa=True)
            
        # Preparar filtros para datas
        # Início data EX
        filtros.filtro_inicio_data_ex = request.POST.get('filtro_inicio_data_ex')
        if filtros.filtro_inicio_data_ex != '':
            try:
                query_proventos = query_proventos.filter(data_ex__gte=datetime.datetime.strptime(filtros.filtro_inicio_data_ex, '%d/%m/%Y'))
            except:
                filtros.filtro_inicio_data_ex = ''
        # Fim data EX
        filtros.filtro_fim_data_ex = request.POST.get('filtro_fim_data_ex')
        if filtros.filtro_fim_data_ex != '':
            try:
                query_proventos = query_proventos.filter(data_ex__lte=datetime.datetime.strptime(filtros.filtro_fim_data_ex, '%d/%m/%Y'))
            except:
                filtros.filtro_fim_data_ex = ''
        # Início data pagamento
        filtros.filtro_inicio_data_pagamento = request.POST.get('filtro_inicio_data_pagamento')
        if filtros.filtro_inicio_data_pagamento != '':
            try:
                query_proventos = query_proventos.filter(data_pagamento__gte=datetime.datetime.strptime(filtros.filtro_inicio_data_pagamento, '%d/%m/%Y'))
            except:
                filtros.filtro_inicio_data_pagamento = ''
        # Fim data pagamento
        filtros.filtro_fim_data_pagamento = request.POST.get('filtro_fim_data_pagamento')
        if filtros.filtro_fim_data_pagamento != '':
            try:
                query_proventos = query_proventos.filter(data_pagamento__lte=datetime.datetime.strptime(filtros.filtro_fim_data_pagamento, '%d/%m/%Y'))
            except:
                filtros.filtro_fim_data_pagamento = ''
    else:
        filtros.filtro_investimento = 'A'
        filtros.filtro_validados = False
        data_ex_inicial = datetime.date.today() - datetime.timedelta(days=365)
        filtros.filtro_inicio_data_ex = data_ex_inicial.strftime('%d/%m/%Y')
        filtros.filtro_fim_data_ex = ''
        filtros.filtro_inicio_data_pagamento = ''
        filtros.filtro_fim_data_pagamento = ''
        
        query_proventos = Provento.gerador_objects.filter(data_ex__gte=data_ex_inicial)
    
    # Buscando ações e fiis relacionados
    if filtros.filtro_investimento == 'A':
        query_proventos = query_proventos.select_related('acao')
    elif filtros.filtro_investimento == 'F':
        query_proventos = query_proventos.select_related('fii')
    
    proventos = list(query_proventos)
    
    if filtros.filtro_investimento == 'A':
        lista_documentos = ProventoAcaoDocumento.objects.filter(provento__in=proventos).select_related('documento')
    elif filtros.filtro_investimento == 'F':
        lista_documentos = ProventoFIIDocumento.objects.filter(provento__in=proventos).select_related('documento')
        
    for provento in proventos:
        if filtros.filtro_investimento == 'A':
            provento.documentos = [documento_acao.documento for documento_acao in lista_documentos if provento.id == documento_acao.provento_id]
        elif filtros.filtro_investimento == 'F':
            provento.documentos = [documento_fii.documento for documento_fii in lista_documentos if provento.id == documento_fii.provento_id]
        for documento in provento.documentos:
            documento.nome = documento.documento.name.split('/')[-1]
            
    return TemplateResponse(request, 'gerador_proventos/listar_proventos.html', {'proventos': proventos, 'filtros': filtros})
        
@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
@adiciona_titulo_descricao('Manual do gerador de proventos', 'Explicações sobre como ler e validar documentos da Bovespa')
def manual_gerador(request, tipo_documento):
    if tipo_documento == 'acao':
        return TemplateResponse(request, 'gerador_proventos/manual_gerador.html', {'max_pendencias': PendenciaDocumentoProvento.MAX_PENDENCIAS_POR_USUARIO})
    elif tipo_documento == 'fii':
        return TemplateResponse(request, 'gerador_proventos/listar_informacoes_geracao_provento_fii.html', {'max_pendencias': PendenciaDocumentoProvento.MAX_PENDENCIAS_POR_USUARIO})
    else:
        raise Http404("Página inválida")
    
    
@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
def puxar_responsabilidade_documento_provento(request):
    investidor = request.user.investidor
    
    id_pendencia = (request.GET.get('id_pendencia') or '').replace('.', '')
    # Verifica se id_pendencia contém apenas números
    if not id_pendencia.isdigit():
        return HttpResponse(json.dumps({'resultado': False, 'mensagem': u'Formato de pendência inválido', 'responsavel': None, 'usuario_responsavel': False}), content_type = "application/json") 
    
    
    # Calcular quantidade de pendências reservadas
    qtd_pendencias_reservadas = InvestidorResponsavelPendencia.objects.filter(investidor=investidor).count()
    if qtd_pendencias_reservadas == PendenciaDocumentoProvento.MAX_PENDENCIAS_POR_USUARIO:
        return HttpResponse(json.dumps({'resultado': False, 'mensagem': u'Você já possui %s pendências reservadas' % (PendenciaDocumentoProvento.MAX_PENDENCIAS_POR_USUARIO), 
                                        'responsavel': None, 'usuario_responsavel': False}), content_type = "application/json") 
    
    # Testa se pendência enviada existe
    try:
        pendencia = PendenciaDocumentoProvento.objects.get(id=id_pendencia)
    except PendenciaDocumentoProvento.DoesNotExist:
        return HttpResponse(json.dumps({'resultado': False, 'mensagem': u'A pendência enviada não existe', 'responsavel': None, 'usuario_responsavel': False}), content_type = "application/json") 
    
    retorno, mensagem = alocar_pendencia_para_investidor(pendencia, investidor)
    # Carregar responsável
    responsavel = PendenciaDocumentoProvento.objects.get(id=id_pendencia).responsavel()
    # Definir responsável
    if responsavel != None:
        usuario_responsavel = True if responsavel.id == investidor.id else False
        responsavel = unicode(responsavel)
    else:
        usuario_responsavel = False
        
    if retorno:
        # Adiciona reserva a quantidade de pendências reservadas
        qtd_pendencias_reservadas += 1
    
    return HttpResponse(json.dumps({'resultado': retorno, 'mensagem': mensagem, 'responsavel': responsavel, 'usuario_responsavel': usuario_responsavel, \
                                    'qtd_pendencias_reservadas': qtd_pendencias_reservadas}), content_type = "application/json") 

@login_required
@user_passes_test(is_superuser)
def reiniciar_documento_proventos(request, id_documento):
    documento = get_object_or_404(DocumentoProventoBovespa, pk=id_documento)
    
    try:
        reiniciar_documento(documento)
        messages.success(request, 'Documento reiniciado com sucesso')
        return HttpResponseRedirect(reverse('gerador_proventos:listar_documentos'))
    except:
        messages.error(request, 'Não foi possível reiniciar documento')
        print traceback.format_exc()
        return HttpResponseRedirect(reverse('gerador_proventos:detalhar_documento', kwargs={'id_documento': id_documento}))
                

@login_required
@user_passes_test(is_superuser)
def relacionar_proventos_fii_add_pelo_sistema(request, id_provento_a_relacionar, id_provento_relacionado):
    try:
        relacionar_proventos_lidos_sistema(ProventoFII.objects.get(id=id_provento_a_relacionar), ProventoFII.objects.get(id=id_provento_relacionado))
        messages.success(request, 'Provento relacionado com sucesso')
        return HttpResponseRedirect(reverse('gerador_proventos:detalhar_provento_fii', kwargs={'id_provento': id_provento_relacionado}))
    except Exception as e:
        messages.error(request, e)
        return HttpResponseRedirect(reverse('gerador_proventos:detalhar_provento_fii', kwargs={'id_provento': id_provento_a_relacionar}))

@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
def remover_responsabilidade_documento_provento(request):
    investidor = request.user.investidor
    
    id_pendencia = (request.GET.get('id_pendencia') or '').replace('.', '')
    # Verifica se id_pendencia contém apenas números
    if not id_pendencia.isdigit():
        return HttpResponse(json.dumps({'resultado': False, 'mensagem': u'Formato de pendência inválido %s' % (id_pendencia)}), content_type = "application/json") 
    
    # Testa se pendência enviada existe
    try:
        pendencia = PendenciaDocumentoProvento.objects.get(id=id_pendencia)
    except PendenciaDocumentoProvento.DoesNotExist:
        return HttpResponse(json.dumps({'resultado': False, 'mensagem': u'A pendência enviada não existe'}), content_type = "application/json") 
    
    retorno, mensagem = desalocar_pendencia_de_investidor(pendencia, investidor)
        
    # Calcular quantidade de pendências reservadas
    qtd_pendencias_reservadas = InvestidorResponsavelPendencia.objects.filter(investidor=investidor).count()
    
    return HttpResponse(json.dumps({'resultado': retorno, 'mensagem': mensagem, 'qtd_pendencias_reservadas': qtd_pendencias_reservadas}), content_type = "application/json") 

@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
@adiciona_titulo_descricao('Validar documento da Bovespa', 'Validar leitura de documento da Bovespa para gerar ações ou apagar o documento')
def validar_documento_provento(request, id_pendencia):
    # Usado para criar objetos vazios
    class Object(object):
        pass
    
    investidor = request.user.investidor
    
    try:
        pendencia = PendenciaDocumentoProvento.objects.select_related('documento__investidorleituradocumento').get(id=id_pendencia)
        # Verificar se pendência é de validação
        if pendencia.tipo != 'V':
            messages.error(request, 'Pendência não é de validação')
            return HttpResponseRedirect(reverse('gerador_proventos:listar_pendencias'))
    except PendenciaDocumentoProvento.DoesNotExist:
        messages.error(request, 'Pendência de validação não foi encontrada')
        return HttpResponseRedirect(reverse('gerador_proventos:listar_pendencias'))
    
    if request.method == 'POST':
        # Verifica se pendência não possuia responsável e usuário acaba de reservá-la
        if request.POST.get('reservar'):
            # Verificar se é reserva ou cancelamento
            if request.POST.get('reservar') == '1':
                # Calcular quantidade de pendências reservadas
                qtd_pendencias_reservadas = InvestidorResponsavelPendencia.objects.filter(investidor=investidor).count()
                if qtd_pendencias_reservadas == PendenciaDocumentoProvento.MAX_PENDENCIAS_POR_USUARIO:
                    messages.error(request, u'Você já possui %s pendências reservadas' % (PendenciaDocumentoProvento.MAX_PENDENCIAS_POR_USUARIO))
                else:
                    # Tentar alocar para o usuário
                    retorno, mensagem = alocar_pendencia_para_investidor(pendencia, investidor)
                    
                    if retorno:
                        # Atualizar pendência
                        pendencia = PendenciaDocumentoProvento.objects.get(id=id_pendencia)
                        messages.success(request, mensagem)
                    else:
                        messages.error(request, mensagem)
            # Cancelamento
            elif request.POST.get('reservar') == '2':
                retorno, mensagem = desalocar_pendencia_de_investidor(pendencia, investidor)
                if retorno:
                    # Atualizar pendência
                    pendencia = PendenciaDocumentoProvento.objects.get(id=id_pendencia)
                    messages.success(request, mensagem)
                else:
                    messages.error(request, mensagem)
                    
        # Testa se o investidor atual é o responsável para mandar POST
        elif investidor != pendencia.investidorresponsavelpendencia.investidor:
            messages.error(request, 'Você não é o responsável por esta pendência')
            return HttpResponseRedirect(reverse('gerador_proventos:listar_pendencias'))
        
#         print request.POST
        if request.POST.get('validar'):
            # Testa se investidor pode validar pendência
            pendencia_finalizada = False
            try:
                with transaction.atomic():
                    salvar_investidor_responsavel_por_validacao(pendencia, investidor)
                    if pendencia.documento.investidorleituradocumento.decisao == 'C':
                        # Ações
                        if pendencia.documento.tipo == 'A':
                            validacao_completa = True
        #                     print 'Validar criação'
                            # Verificar proventos descritos na pendência
                            proventos_documento = ProventoAcaoDocumento.objects.filter(documento=pendencia.documento)
                            descricoes_proventos = ProventoAcaoDescritoDocumentoBovespa.objects.filter(id__in=proventos_documento.values_list('descricao_provento', flat=True))
                            # Guarda as descrições que foram apontadas como relacionadas a algum provento
                            proventos_relacionados = {}
                            for descricao in descricoes_proventos:
                                # Testar se ID's de descrições foram marcados para relacionamento, se sim, deve ter um provento relacionado
                                # Verifica se é alteração
                                if str(descricao.id) in request.POST.keys():
                                    # Se sim, alterar números de versão
        #                             print 'Alterou', descricao.id
                                    if request.POST.get('descricao_%s' % (descricao.id)):
                                        # Verificar se foi relacionado a um provento ou a uma descrição
                                        provento_relacionado = Provento.gerador_objects.get(id=request.POST.get('descricao_%s' % (descricao.id)))
        #                                 print u'Descrição %s é relacionada a %s' % (descricao.id, provento_relacionado)
                                        proventos_relacionados[descricao] = provento_relacionado
                                    else:
                                        validacao_completa = False
                                        messages.error(request, 'Provento de identificador %s marcado como relacionado a outro provento, escolha um provento para a relação' % (descricao.id))
                                        continue
                            if validacao_completa:
        #                         print 'Validação completa'
                                try:
                                    with transaction.atomic():
                                        # Salva versões alteradas para os provento_documentos
                                        for descricao, provento in proventos_relacionados.items():
                                            versionar_descricoes_relacionadas_acoes(descricao, provento)
                                        # Altera proventos para serem oficiais
                                        for provento_id in ProventoAcaoDocumento.objects.filter(documento=pendencia.documento).values_list('provento', flat=True):
                                            provento = Provento.gerador_objects.get(id=provento_id)
                                            if not provento.oficial_bovespa:
                                                provento.oficial_bovespa = True
                                                provento.save()
                                        pendencia_finalizada = True
                                except:
                                    if settings.ENV == 'PROD':
                                        mail_admins(u'Erro em Validar provento de ações', traceback.format_exc().decode('utf-8'))
                                    elif settings.ENV == 'DEV':
                                        print traceback.format_exc()
                                    messages.error(request, 'Houve erro no relacionamento de proventos')
                                    raise ValueError('Não foi possível validar provento')
                            # Qualquer erro que deixe a validação incompleta faz necessário desfazer investidor responsável pela validação
                            else:
                                # Jogar erro para dar rollback na transação
                                raise ValueError('Não foi possível validar provento')
                            
                        # FII
                        elif pendencia.documento.tipo == 'F':
                            validacao_completa = True
        #                     print 'Validar criação'
                            # Verificar proventos descritos na pendência
                            proventos_documento = ProventoFIIDocumento.objects.filter(documento=pendencia.documento)
                            descricoes_proventos = ProventoFIIDescritoDocumentoBovespa.objects.filter(id__in=proventos_documento.values_list('descricao_provento', flat=True))
                            # Guarda as descrições que foram apontadas como relacionadas a algum provento
                            proventos_relacionados = {}
                            for descricao in descricoes_proventos:
                                # Testar se ID's de descrições foram marcados para relacionamento, se sim, deve ter um provento relacionado
                                # Verifica se é alteração
                                if str(descricao.id) in request.POST.keys():
                                    # Se sim, alterar números de versão
        #                             print 'Alterou', descricao.id
                                    if request.POST.get('descricao_%s' % (descricao.id)):
                                        # Verificar se foi relacionado a um provento ou a uma descrição
                                        provento_relacionado = ProventoFII.gerador_objects.get(id=request.POST.get('descricao_%s' % (descricao.id)))
        #                                 print u'Descrição %s é relacionada a %s' % (descricao.id, provento_relacionado)
                                        proventos_relacionados[descricao] = provento_relacionado
                                    else:
                                        validacao_completa = False
                                        messages.error(request, 'Provento de identificador %s marcado como relacionado a outro provento, escolha um provento para a relação' % (descricao.id))
                                        continue
                            if validacao_completa:
        #                         print 'Validação completa'
                                try:
                                    with transaction.atomic():
                                        # Salva versões alteradas para os provento_documentos
                                        for descricao, provento in proventos_relacionados.items():
                                            versionar_descricoes_relacionadas_fiis(descricao, provento)
                                        # Altera proventos para serem oficiais
                                        for provento_id in ProventoFIIDocumento.objects.filter(documento=pendencia.documento).values_list('provento', flat=True):
                                            provento = ProventoFII.gerador_objects.get(id=provento_id)
                                            if not provento.oficial_bovespa:
                                                provento.oficial_bovespa = True
                                                provento.save()
                                        pendencia_finalizada = True
                                except:
                                    if settings.ENV == 'PROD':
                                        mail_admins(u'Erro em Validar provento de FIIs', traceback.format_exc().decode('utf-8'))
                                    elif settings.ENV == 'DEV':
                                        print traceback.format_exc()
                                    messages.error(request, 'Houve erro no relacionamento de proventos')
                                    raise ValueError('Não foi possível validar provento')
                            # Qualquer erro que deixe a validação incompleta faz necessário desfazer investidor responsável pela validação
                            else:
                                # Jogar erro para dar rollback na transação
                                raise ValueError('Não foi possível validar provento')
                                    
                    elif pendencia.documento.investidorleituradocumento.decisao == 'E':
                        # Apagar documento
                        pendencia.documento.apagar_documento()
                        pendencia_finalizada = True
                        
                # Verifica se validação passou ou foi feita uma exclusão
                if pendencia_finalizada:
                    # Remover pendência
                    pendencia.delete()
                    messages.success(request, 'Pendência validada com sucesso')
                    return HttpResponseRedirect(reverse('gerador_proventos:listar_pendencias'))
            except:
                if settings.ENV == 'PROD':
                    mail_admins(u'Erro em Validar provento', traceback.format_exc().decode('utf-8'))
                elif settings.ENV == 'DEV':
                    print traceback.format_exc()
        
        elif request.POST.get('recusar'):
#             print 'Recusar'
            # Verificar se texto de recusa foi preenchido
            motivo_recusa = request.POST.get('motivo_recusa')
            # Criar vínculo de responsabilidade por recusa
            try:
                salvar_investidor_responsavel_por_recusar_documento(pendencia, investidor, motivo_recusa)
                messages.success(request, 'Pendência recusada com sucesso')
                return HttpResponseRedirect(reverse('gerador_proventos:listar_pendencias'))
            except Exception as erro:
                messages.error(request, unicode(erro))
        
    # Mostrar decisão de criar proventos
    if pendencia.documento.investidorleituradocumento.decisao == 'C':
        if pendencia.documento.tipo == 'A':
            proventos_documento = ProventoAcaoDocumento.objects.filter(documento=pendencia.documento).values_list('descricao_provento', flat=True)
            descricoes_proventos = ProventoAcaoDescritoDocumentoBovespa.objects.filter(id__in=proventos_documento).select_related('proventoacaodocumento__provento')
            for descricao_provento in descricoes_proventos:
                # Definir tipo de provento
                if descricao_provento.tipo_provento == 'A':
                    descricao_provento.acoes_recebidas = descricao_provento.acaoproventoacaodescritodocumentobovespa_set.all()
                    # Remover 0s a direita para valores
    #                 for acao_descricao_provento in descricao_provento.acoes_recebidas:
    #                     acao_descricao_provento.valor_calculo_frac = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(acao_descricao_provento.valor_calculo_frac))
                
                # Remover 0s a direita para valores
                descricao_provento.valor_unitario = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(descricao_provento.valor_unitario))
                
                # Buscar proventos próximos
                descricao_provento.proventos_proximos = buscar_proventos_proximos_acao(descricao_provento)
                for provento_proximo in descricao_provento.proventos_proximos:
                    # Definir tipo de provento
                    if provento_proximo.tipo_provento == 'A':
                        provento_proximo.acoes_recebidas = provento_proximo.acaoprovento_set.all()
                        # Remover 0s a direita para valores
                        for acao_descricao_provento in provento_proximo.acoes_recebidas:
                            acao_descricao_provento.valor_calculo_frac = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(acao_descricao_provento.valor_calculo_frac))
                    
                    # Remover 0s a direita para valores
                    provento_proximo.valor_unitario = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(provento_proximo.valor_unitario))
                            
            # Descrição da decisão do responsável pela leitura
            pendencia.decisao = 'Criar %s provento(s)' % (ProventoAcaoDocumento.objects.filter(documento=pendencia.documento).count())
        elif pendencia.documento.tipo == 'F':
            proventos_documento = ProventoFIIDocumento.objects.filter(documento=pendencia.documento).values_list('descricao_provento', flat=True)
            descricoes_proventos = ProventoFIIDescritoDocumentoBovespa.objects.filter(id__in=proventos_documento).select_related('proventofiidocumento__provento')
            for descricao_provento in descricoes_proventos:
                # Remover 0s a direita para valores
                descricao_provento.valor_unitario = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(descricao_provento.valor_unitario))
                
                # Buscar proventos próximos
                descricao_provento.proventos_proximos = buscar_proventos_proximos_fii(descricao_provento)
                for provento_proximo in descricao_provento.proventos_proximos:
                    # Remover 0s a direita para valores
                    provento_proximo.valor_unitario = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(provento_proximo.valor_unitario))
                            
            # Descrição da decisão do responsável pela leitura
            pendencia.decisao = 'Criar %s provento(s)' % (ProventoFIIDocumento.objects.filter(documento=pendencia.documento).count())
            
    # Mostrar decisão de excluir documentos
    elif pendencia.documento.investidorleituradocumento.decisao == 'E':
        descricoes_proventos = {}
        
        # Descrição da decisão do responsável pela leitura
        pendencia.decisao = 'Excluir documento'
    
    # Área de infomações úteis
    if pendencia.documento.tipo == 'A':
        # Preparar informações sobre negociação das ações que são mostradas como opção
        infos_uteis = {'historico_negociacao': list()}
        for acao in Acao.objects.filter(empresa=pendencia.documento.empresa):
            try:
                negociacao_acao = Object()
                negociacao_acao.ticker = acao.ticker
                negociacao_acao.inicio = HistoricoAcao.objects.filter(oficial_bovespa=True, acao=acao).order_by('data')[0].data
                negociacao_acao.fim = HistoricoAcao.objects.filter(oficial_bovespa=True, acao=acao).order_by('-data')[0].data
                infos_uteis['historico_negociacao'].append(negociacao_acao)
            except:
                pass
        
        # Se histórico de negociação estiver vazio, removê-lo
        if len(infos_uteis['historico_negociacao']) == 0:
            del infos_uteis['historico_negociacao']
    elif pendencia.documento.tipo == 'F':
        infos_uteis = {}
    
    return TemplateResponse(request, 'gerador_proventos/validar_documento_provento.html', {'pendencia': pendencia, 'descricoes_proventos': descricoes_proventos, 
                                                                                           'infos_uteis': infos_uteis})