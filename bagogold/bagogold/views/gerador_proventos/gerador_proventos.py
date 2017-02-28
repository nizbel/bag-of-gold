# -*- coding: utf-8 -*-
from bagogold import settings
from bagogold.bagogold.forms.gerador_proventos import \
    ProventoAcaoDescritoDocumentoBovespaForm, \
    AcaoProventoAcaoDescritoDocumentoBovespaForm, \
    ProventoFIIDescritoDocumentoBovespaForm
from bagogold.bagogold.models.acoes import Acao, Provento, AcaoProvento
from bagogold.bagogold.models.empresa import Empresa
from bagogold.bagogold.models.fii import ProventoFII, FII
from bagogold.bagogold.models.gerador_proventos import DocumentoProventoBovespa, \
    PendenciaDocumentoProvento, ProventoAcaoDescritoDocumentoBovespa, \
    ProventoAcaoDocumento, InvestidorResponsavelPendencia, \
    AcaoProventoAcaoDescritoDocumentoBovespa, ProventoFIIDocumento, \
    ProventoFIIDescritoDocumentoBovespa
from bagogold.bagogold.utils.gerador_proventos import \
    alocar_pendencia_para_investidor, desalocar_pendencia_de_investidor, \
    salvar_investidor_responsavel_por_leitura, criar_descricoes_provento_acoes, \
    desfazer_investidor_responsavel_por_leitura, buscar_proventos_proximos_acao, \
    versionar_descricoes_relacionadas_acoes, \
    salvar_investidor_responsavel_por_validacao, \
    desfazer_investidor_responsavel_por_validacao, \
    salvar_investidor_responsavel_por_recusar_documento
from bagogold.bagogold.utils.misc import \
    formatar_zeros_a_direita_apos_2_casas_decimais
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.urlresolvers import reverse
from django.forms.formsets import formset_factory
from django.forms.models import model_to_dict
from django.http.response import HttpResponseRedirect, HttpResponse, Http404
from django.template.response import TemplateResponse
import json
import os

@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
def baixar_documento_provento(request, id_documento):
    try:
        documento_provento = DocumentoProventoBovespa.objects.get(id=id_documento)
    except DocumentoProventoBovespa.DoesNotExist:
        messages.error(request, 'Documento não foi encontrado para download')
        return HttpResponseRedirect(reverse('listar_pendencias'))
    filename = documento_provento.documento.name.split('/')[-1]
    if documento_provento.extensao_documento() == 'doc':
        response = HttpResponse(documento_provento.documento, content_type='application/msword')
    else:
        response = HttpResponse(documento_provento.documento, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    response['Content-Length'] = os.path.getsize(settings.MEDIA_ROOT + documento_provento.documento.name)

    return response

@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
def detalhar_documento(request, id_documento):
    documento = DocumentoProventoBovespa.objects.get(id=id_documento)
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
            provento.versao = provento.proventoacaodocumento.versao
        
    return TemplateResponse(request, 'gerador_proventos/detalhar_documento.html', {'documento': documento, 'proventos': proventos})

@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
def detalhar_provento_acao(request, id_provento):
    provento = Provento.gerador_objects.get(id=id_provento)
    
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
        versoes = ProventoAcaoDescritoDocumentoBovespa.objects.filter(proventoacaodocumento__provento=provento).order_by('proventoacaodocumento__versao')
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
def detalhar_provento_fii(request, id_provento):
    provento = ProventoFII.gerador_objects.get(id=id_provento)
    
    # Remover 0s a direita para valores
    provento.valor_unitario = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(provento.valor_unitario))
    # Adicionar informação de versão
    provento.versao = provento.proventofiidocumento.versao
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
def ler_documento_provento(request, id_pendencia):
    try:
        pendencia = PendenciaDocumentoProvento.objects.get(id=id_pendencia)
        # Verificar se pendência é de leitura
        if pendencia.tipo != 'L':
            messages.success(request, 'Pendência não é de leitura')
            return HttpResponseRedirect(reverse('listar_pendencias'))
    except PendenciaDocumentoProvento.DoesNotExist:
        messages.error(request, 'Pendência de leitura não foi encontrada')
        return HttpResponseRedirect(reverse('listar_pendencias'))
        
    investidor = request.user.investidor
    
    # Verifica se pendência já possui proventos descritos (foi feita recusa)
    # Para ações
    if pendencia.documento.tipo == 'A':
        form_extra = 0 if ProventoAcaoDocumento.objects.filter(documento=pendencia.documento).exists() else 1
        ProventoFormset = formset_factory(ProventoAcaoDescritoDocumentoBovespaForm, extra=form_extra)
        AcaoProventoFormset = formset_factory(AcaoProventoAcaoDescritoDocumentoBovespaForm, extra=form_extra)
    # PAra FIIs
    elif pendencia.documento.tipo == 'F':
        form_extra = 0 if ProventoFIIDocumento.objects.filter(documento=pendencia.documento).exists() else 1
        ProventoFormset = formset_factory(ProventoFIIDescritoDocumentoBovespaForm, extra=form_extra)
    
    if request.method == 'POST':
        # Verifica se pendência não possuia responsável e usuário acaba de reservá-la
        if request.POST.get('reservar'):
            # Calcular quantidade de pendências reservadas
            qtd_pendencias_reservadas = InvestidorResponsavelPendencia.objects.filter(investidor=investidor).count()
            if qtd_pendencias_reservadas == 20:
                messages.error(request, u'Você já possui 20 pendências reservadas')
            else:
                # Tentar alocar para o usuário
                retorno, mensagem = alocar_pendencia_para_investidor(pendencia, investidor)
                
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
            elif pendencia.documento.tipo == 'F':
                formset_provento = ProventoFormset(prefix='provento')
                formset_acao_provento = {}
            
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
                
        # Caso o botão de salvar ter sido apertado
        elif request.POST.get('save'):
            # Radio de documento estava em Gerar
            if request.POST['radioDocumento'] == '1':
#                 print request.POST
                formset_provento = ProventoFormset(request.POST, prefix='provento')
                formset_acao_provento = AcaoProventoFormset(request.POST, prefix='acao_provento')
                
                # Apaga descrições que já existam para poder rodar validações, serão posteriormente readicionadas caso haja algum erro
                info_proventos_a_apagar = list(ProventoAcaoDocumento.objects.filter(documento=pendencia.documento)) \
                    + list(AcaoProvento.objects.filter(provento__id__in=ProventoAcaoDocumento.objects.filter(documento=pendencia.documento).values_list('provento', flat=True))) \
                    + list(Provento.gerador_objects.filter(id__in=ProventoAcaoDocumento.objects.filter(documento=pendencia.documento).values_list('provento', flat=True))) \
                    + list(AcaoProventoAcaoDescritoDocumentoBovespa.objects.filter(provento__id__in=ProventoAcaoDocumento.objects.filter(documento=pendencia.documento).values_list('descricao_provento', flat=True))) \
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
                    # Guarda os proventos e ações de proventos criadas para salvar caso todos os formulários sejam válidos
                    proventos_validos = list()
                    acoes_proventos_validos = list()
                    for form_provento in formset_provento:
                        provento = form_provento.save(commit=False)
#                         print provento
                        proventos_validos.append(provento)
                        form_acao_provento = formset_acao_provento[indice_provento]
                        # Verificar a ação do provento em ações
                        if provento.tipo_provento == 'A':
                            acao_provento = form_acao_provento.save(commit=False) if form_acao_provento.is_valid() and form_acao_provento.has_changed() else None
                            if acao_provento == None:
                                forms_validos = False
                            else:
                                acao_provento.provento = provento
#                                 print acao_provento
                                acoes_proventos_validos.append(acao_provento)
                        indice_provento += 1
                    if forms_validos:
                        try:
                            # Colocar investidor como responsável pela leitura do documento
                            salvar_investidor_responsavel_por_leitura(pendencia, investidor, decisao='C')
                            # Salvar descrições de proventos
                            criar_descricoes_provento_acoes(proventos_validos, acoes_proventos_validos, pendencia.documento)
                            messages.success(request, 'Descrições de proventos criadas com sucesso')
                            return HttpResponseRedirect(reverse('listar_pendencias'))
                        except Exception as e:
                            desfazer_investidor_responsavel_por_leitura(pendencia, investidor)
                            messages.error(request, str(e))
                    else:
                        messages.error(request, 'Proventos em ações não conferem com os proventos criados')
                
                # Readiciona proventos para o caso de não haver logrado sucesso na leitura
                for elemento in list(reversed(info_proventos_a_apagar)):
                    elemento.save()
                
                # Testando erros
                print dir(formset_provento.errors)
                print formset_provento.errors, formset_provento.non_form_errors()
                for form in formset_provento:
                    for erro in form.non_field_errors():
                        messages.error(request, erro)
                
            # Radio de documento estava em Excluir
            elif request.POST['radioDocumento'] == '0':
                # Colocar investidor como responsável pela leitura do documento
                salvar_investidor_responsavel_por_leitura(pendencia, investidor, decisao='E')
                messages.success(request, 'Exclusão de arquivo registrada com sucesso')
                return HttpResponseRedirect(reverse('listar_pendencias'))
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
    
        
        elif pendencia.documento.tipo == 'F':
            # Proventos de FII
            proventos_iniciais = list()
            for provento_fii_documento in pendencia.documento.proventofiidocumento_set.all():
                proventos_iniciais.append(model_to_dict(provento_fii_documento.descricao_provento))
            formset_provento = ProventoFormset(prefix='provento', initial=proventos_iniciais)
            formset_acao_provento = {}
            
    # Preparar opções de busca, tanto para POST quanto para GET
    if pendencia.documento.tipo == 'A':
        for form in formset_provento:
            form.fields['acao'].queryset = Acao.objects.filter(empresa=pendencia.documento.empresa)
    elif pendencia.documento.tipo == 'F':
        for form in formset_provento:
            form.fields['fii'].queryset = FII.objects.filter(empresa=pendencia.documento.empresa)
    
    # Preparar motivo de recusa, caso haja
    recusa = pendencia.documento.ultima_recusa()
    
    return TemplateResponse(request, 'gerador_proventos/ler_documento_provento.html', {'pendencia': pendencia, 'formset_provento': formset_provento, 'formset_acao_provento': formset_acao_provento, \
                                                                                       'recusa': recusa})
    
@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
def listar_documentos(request):
    empresa_id = Empresa.objects.all().order_by('id').values_list('id', flat=True)[0]
    if request.method == 'POST':
        if request.POST.get("busca_empresa"):
            empresa_id = Empresa.objects.get(id=request.POST['busca_empresa']).id
    
    # Mostrar empresa atual
    empresa_atual = Empresa.objects.get(id=empresa_id)
    
    empresas = Empresa.objects.all().order_by('nome')

    documentos = DocumentoProventoBovespa.objects.filter(empresa__id=empresa_id).order_by('data_referencia')
    
    for documento in documentos:
        if documento.tipo == 'A':
            documento.ha_proventos_vinculados = documento.proventoacaodocumento_set.count() > 0
            
        # Preparar descrição de tipos
        documento.tipo = 'Ação' if documento.tipo == 'A' else 'FII'
            
    return TemplateResponse(request, 'gerador_proventos/listar_documentos.html', {'documentos': documentos, 'empresas': empresas, 'empresa_atual': empresa_atual})


@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
def listar_pendencias(request):
    # Usado para criar objetos vazios
    class Object(object):
        pass
    
    investidor = request.user.investidor
    
    # Valor padrão para o filtro de quantidade
    filtros = Object()
    # Prepara a busca
    query_pendencias = PendenciaDocumentoProvento.objects.all() 
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
    else:
        filtros.filtro_qtd = 200
        filtros.filtro_tipo_leitura = True
        filtros.filtro_tipo_validacao = True
        filtros.filtro_reservaveis = True
        
    # Filtrar
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
    
    for pendencia in pendencias:
        pendencia.nome = pendencia.documento.documento.name.split('/')[-1]
        pendencia.tipo_documento = 'Ação' if pendencia.documento.tipo == 'A' else 'FII'
        pendencia.tipo_pendencia = 'Leitura' if pendencia.tipo == 'L' else 'Validação'
        pendencia.responsavel = pendencia.responsavel()
        
    return TemplateResponse(request, 'gerador_proventos/listar_pendencias.html', {'pendencias': pendencias, 'qtd_pendencias_reservadas': qtd_pendencias_reservadas,'filtros': filtros})


@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
def listar_proventos(request):
    proventos = list(Provento.gerador_objects.all())
    proventos.extend(list(ProventoFII.gerador_objects.all()))
    
    for provento in proventos:
        if isinstance(provento, Provento):
            provento.documentos = DocumentoProventoBovespa.objects.filter(id__in=provento.proventoacaodocumento_set.values_list('documento', flat=True))
        elif isinstance(provento, ProventoFII):
            provento.documentos = DocumentoProventoBovespa.objects.filter(id__in=provento.proventofiidocumento_set.values_list('documento', flat=True))
        for documento in provento.documentos:
            documento.nome = documento.documento.name.split('/')[-1]
        
    return TemplateResponse(request, 'gerador_proventos/listar_proventos.html', {'proventos': proventos})
        
@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
def manual_gerador(request, tipo_documento):
    if tipo_documento == 'acao':
        return TemplateResponse(request, 'gerador_proventos/manual_gerador.html')
    elif tipo_documento == 'fii':
        return TemplateResponse(request, 'gerador_proventos/listar_informacoes_geracao_provento_fii.html')
    else:
        raise Http404("Página inválida")
    
    
@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
def puxar_responsabilidade_documento_provento(request):
    investidor = request.user.investidor
    
    id_pendencia = request.GET['id_pendencia'].replace('.', '')
    # Verifica se id_pendencia contém apenas números
    if not id_pendencia.isdigit():
        return HttpResponse(json.dumps({'resultado': False, 'mensagem': u'Formato de pendência inválido', 'responsavel': None, 'usuario_responsavel': False}), content_type = "application/json") 
    
    
    # Calcular quantidade de pendências reservadas
    qtd_pendencias_reservadas = InvestidorResponsavelPendencia.objects.filter(investidor=investidor).count()
    if qtd_pendencias_reservadas == 20:
        return HttpResponse(json.dumps({'resultado': False, 'mensagem': u'Você já possui 20 pendências reservadas', 'responsavel': None, 'usuario_responsavel': False}), content_type = "application/json") 
    
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
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
def remover_responsabilidade_documento_provento(request):
    investidor = request.user.investidor
    
    id_pendencia = request.GET['id_pendencia'].replace('.', '')
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
def validar_documento_provento(request, id_pendencia):
    investidor = request.user.investidor
    
    try:
        pendencia = PendenciaDocumentoProvento.objects.get(id=id_pendencia)
        # Verificar se pendência é de validação
        if pendencia.tipo != 'V':
            messages.error(request, 'Pendência não é de validação')
            return HttpResponseRedirect(reverse('listar_pendencias'))
    except PendenciaDocumentoProvento.DoesNotExist:
        messages.error(request, 'Pendência de validação não foi encontrada')
        return HttpResponseRedirect(reverse('listar_pendencias'))
    
    if request.method == 'POST':
        # Verifica se pendência não possuia responsável e usuário acaba de reservá-la
        if request.POST.get('reservar'):
            # Calcular quantidade de pendências reservadas
            qtd_pendencias_reservadas = InvestidorResponsavelPendencia.objects.filter(investidor=investidor).count()
            if qtd_pendencias_reservadas == 20:
                messages.error(request, u'Você já possui 20 pendências reservadas')
            else:
                # Tentar alocar para o usuário
                retorno, mensagem = alocar_pendencia_para_investidor(pendencia, investidor)
                
                if retorno:
                    # Atualizar pendência
                    pendencia = PendenciaDocumentoProvento.objects.get(id=id_pendencia)
                    messages.success(request, mensagem)
                else:
                    messages.error(request, mensagem)
                    
        # Testa se o investidor atual é o responsável para mandar POST
        elif investidor != pendencia.investidorresponsavelpendencia.investidor:
            messages.error(request, 'Você não é o responsável por esta pendência')
            return HttpResponseRedirect(reverse('listar_pendencias'))
        
#         print request.POST
        if request.POST.get('validar'):
            # Testa se investidor pode validar pendência
            investidor_pode_validar = True
            try:
                salvar_investidor_responsavel_por_validacao(pendencia, investidor)
            except ValueError as erro:
                desfazer_investidor_responsavel_por_validacao(pendencia, investidor)
                messages.error(request, str(erro))
                investidor_pode_validar = False
                
            if investidor_pode_validar:
                if pendencia.documento.investidorleituradocumento.decisao == 'C':
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
                            # Salva versões alteradas para os provento_documentos
                            for descricao, provento in proventos_relacionados.items():
                                versionar_descricoes_relacionadas_acoes(descricao, provento)
                            # Altera proventos para serem oficiais
                            for provento_id in ProventoAcaoDocumento.objects.filter(documento=pendencia.documento).values_list('provento', flat=True):
                                provento = Provento.gerador_objects.get(id=provento_id)
                                if not provento.oficial_bovespa:
                                    provento.oficial_bovespa = True
                                    provento.save()
                        except:
                            messages.error(request, 'Houve erro no relacionamento de proventos')
                            desfazer_investidor_responsavel_por_validacao(pendencia, investidor)
                    # Qualquer erro que deixe a validação incompleta faz necessário desfazer investidor responsável pela validação
                    else:
                        desfazer_investidor_responsavel_por_validacao(pendencia, investidor)
                                
                elif pendencia.documento.investidorleituradocumento.decisao == 'E':
#                     print 'Validar exclusão'
                    # Apagar documento
                    pendencia.documento.apagar_documento()
                    
                # Verifica se validação passou ou foi feita uma exclusão
                if pendencia.documento.investidorleituradocumento.decisao == 'E' or (validacao_completa and pendencia.documento.investidorleituradocumento.decisao == 'C'):
                    # Remover pendência
                    pendencia.delete()
                    messages.success(request, 'Pendência validada com sucesso')
                    return HttpResponseRedirect(reverse('listar_pendencias'))
        
        elif request.POST.get('recusar'):
#             print 'Recusar'
            # Verificar se texto de recusa foi preenchido
            motivo_recusa = request.POST.get('motivo_recusa')
            # Criar vínculo de responsabilidade por recusa
            try:
                salvar_investidor_responsavel_por_recusar_documento(pendencia, investidor, motivo_recusa)
                messages.success(request, 'Pendência recusada com sucesso')
                return HttpResponseRedirect(reverse('listar_pendencias'))
            except Exception as erro:
                messages.error(request, unicode(erro))
        
    if pendencia.documento.investidorleituradocumento.decisao == 'C':
        proventos_documento = ProventoAcaoDocumento.objects.filter(documento=pendencia.documento).values_list('descricao_provento', flat=True)
        descricoes_proventos = ProventoAcaoDescritoDocumentoBovespa.objects.filter(id__in=proventos_documento)
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
    elif pendencia.documento.investidorleituradocumento.decisao == 'E':
        descricoes_proventos = {}
        
        # Descrição da decisão do responsável pela leitura
        pendencia.decisao = 'Excluir documento'
    
    return TemplateResponse(request, 'gerador_proventos/validar_documento_provento.html', {'pendencia': pendencia, 'descricoes_proventos': descricoes_proventos})