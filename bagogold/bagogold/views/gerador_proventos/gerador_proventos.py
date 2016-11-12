# -*- coding: utf-8 -*-
from bagogold import settings
from bagogold.bagogold.forms.gerador_proventos import \
    ProventoAcaoDescritoDocumentoBovespaForm, \
    AcaoProventoAcaoDescritoDocumentoBovespaForm
from bagogold.bagogold.models.acoes import Acao
from bagogold.bagogold.models.empresa import Empresa
from bagogold.bagogold.models.gerador_proventos import DocumentoProventoBovespa, \
    PendenciaDocumentoProvento, ProventoAcaoDescritoDocumentoBovespa, \
    ProventoAcaoDocumento
from bagogold.bagogold.utils.gerador_proventos import \
    alocar_pendencia_para_investidor, desalocar_pendencia_de_investidor, \
    salvar_investidor_responsavel_por_leitura, criar_descricoes_provento_acoes, \
    retornar_investidor_responsavel_por_leitura
from bagogold.bagogold.utils.investidores import is_superuser
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test, \
    permission_required
from django.core.urlresolvers import reverse
from django.forms.formsets import formset_factory
from django.http.response import HttpResponseRedirect, HttpResponse
from django.template.response import TemplateResponse
import json
import os

@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
def baixar_documento_provento(request, id_documento):
    documento_provento = DocumentoProventoBovespa.objects.get(id=id_documento)
    filename = documento_provento.documento.name.split('/')[-1]
    response = HttpResponse(documento_provento.documento, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    response['Content-Length'] = os.path.getsize(settings.MEDIA_ROOT + documento_provento.documento.name)

    return response

@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
def ler_documento_provento(request, id_pendencia):
    pendencia = PendenciaDocumentoProvento.objects.get(id=id_pendencia)
    # Verificar se pendência é de leitura
    if pendencia.tipo != 'L':
        messages.success(request, 'Pendência não é de leitura')
        return HttpResponseRedirect(reverse('listar_pendencias'))
    
    investidor = request.user.investidor
    
    # Preencher responsável
    pendencia.responsavel = pendencia.responsavel() or 'Sem responsável'
    
    ProventoFormset = formset_factory(ProventoAcaoDescritoDocumentoBovespaForm)
    AcaoProventoFormset = formset_factory(AcaoProventoAcaoDescritoDocumentoBovespaForm)
    
    if request.method == 'POST':
        if request.POST.get('preparar_proventos'):
            if request.POST['num_proventos'].isdigit():
                qtd_proventos = int(request.POST['num_proventos']) if int(request.POST['num_proventos']) <= 10 else 1
                ProventoFormset = formset_factory(ProventoAcaoDescritoDocumentoBovespaForm, extra=qtd_proventos)
                AcaoProventoFormset = formset_factory(AcaoProventoAcaoDescritoDocumentoBovespaForm, extra=qtd_proventos)
                formset_provento = ProventoFormset(prefix='provento')
                formset_acao_provento = AcaoProventoFormset(prefix='acao_provento')
                
        # Caso o botão de salvar ter sido apertado
        elif request.POST.get('save'):
            # Radio de documento estava em Gerar
            if request.POST['radioDocumento'] == 'Gerar':
                formset_provento = ProventoFormset(request.POST, prefix='provento')
                formset_acao_provento = AcaoProventoFormset(request.POST, prefix='acao_provento')
                
                if formset_provento.is_valid():
                    # Verifica se dados inseridos são todos válidos
                    forms_validos = True
                    indice_provento = 0
                    # Guarda os proventos e ações de proventos criadas para salvar caso todos os formulários sejam válidos
                    proventos_validos = list()
                    acoes_proventos_validos = list()
                    for form_provento in formset_provento:
                        provento = form_provento.save(commit=False)
                        print provento
                        proventos_validos.append(provento)
                        form_acao_provento = formset_acao_provento[indice_provento]
                        # Verificar a ação do provento em ações
                        if provento.tipo_provento == 'A':
                            acao_provento = form_acao_provento.save(commit=False) if form_acao_provento.is_valid() and form_acao_provento.has_changed() else None
                            if acao_provento == None:
                                forms_validos = False
                            else:
                                acao_provento.provento = provento
                                print acao_provento
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
                            retornar_investidor_responsavel_por_leitura(pendencia, investidor)
                            messages.error(request, str(e))
                    else:
                        messages.error(request, 'Proventos em ações não conferem com os proventos criados')
                        
            # Radio de documento estava em Excluir
            elif request.POST['radioDocumento'] == 'Excluir':
                # Colocar investidor como responsável pela leitura do documento
                salvar_investidor_responsavel_por_leitura(pendencia, investidor, decisao='E')
                messages.success(request, 'Exclusão de arquivo registrada com sucesso')
                return HttpResponseRedirect(reverse('listar_pendencias'))
    else:
        # Preparar formset de proventos
        if pendencia.documento.tipo == 'A':
            formset_provento = ProventoFormset(prefix='provento')
            formset_acao_provento = AcaoProventoFormset(prefix='acao_provento')
    
    for form in formset_provento:
        form.fields['acao'].queryset = Acao.objects.filter(empresa=pendencia.documento.empresa)
    
    return TemplateResponse(request, 'gerador_proventos/ler_documento_provento.html', {'pendencia': pendencia, 'formset_provento': formset_provento, 'formset_acao_provento': formset_acao_provento})
    
@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
def listar_documentos(request):
    empresa_id = Empresa.objects.all().order_by('id').values_list('id', flat=True)[0]
    if request.method == 'POST':
        if request.POST.get("busca_empresa"):
            empresa_id = Acao.objects.filter(ticker__istartswith=request.POST['busca_empresa'])[0].empresa.id
    
    # Mostrar empresa atual
    empresa_atual = Empresa.objects.get(id=empresa_id)
    empresa_atual.ticker = empresa_atual.ticker_empresa()
    
    empresas = [empresa.ticker_empresa() for empresa in Empresa.objects.all().order_by('id')]
#     empresas = map(str, empresas)
    empresas = '["' + '","'.join(empresas) + '"]'
    documentos = DocumentoProventoBovespa.objects.filter(empresa__id=empresa_id).order_by('data_referencia')
    
    for documento in documentos:
        documento.nome = documento.documento.name.split('/')[-1]
        
        documento.pendente = documento.pendente()
        
        if documento.tipo == 'A':
            documento.ha_proventos_vinculados = False
            
        # Preparar descrição de tipos
        documento.tipo = 'Ação' if documento.tipo == 'A' else 'FII'
            
    return TemplateResponse(request, 'gerador_proventos/listar_documentos.html', {'documentos': documentos, 'empresas': empresas, 'empresa_atual': empresa_atual})

@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
def listar_pendencias(request):
    # Testa se há página inicial
#     if 'pagina_atual_lista_pendencias' in request.session:
#         pagina_inicial = request.session['pagina_atual_lista_pendencias']
#         print 'pagina inicial', pagina_inicial
#         # Testa se página inicial é feita de dígitos numéricos
#         if not pagina_inicial.isdigit():
#             pagina_inicial = '0'
#         # Remover pagina inicial da sessão para não atrapalhar futuras iterações com a página
#         del request.session['pagina_atual_lista_pendencias']
#     else:
#     pagina_inicial = '0'
        
    pendencias = PendenciaDocumentoProvento.objects.all()
    
    for pendencia in pendencias:
        pendencia.nome = pendencia.documento.documento.name.split('/')[-1]
        pendencia.tipo_documento = 'Ação' if pendencia.documento.tipo == 'A' else 'FII'
        pendencia.tipo_pendencia = 'Leitura' if pendencia.tipo == 'L' else 'Validação'
        pendencia.responsavel = pendencia.responsavel()
        
    return TemplateResponse(request, 'gerador_proventos/listar_pendencias.html', {'pendencias': pendencias})


@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
def listar_proventos(request):
    pass

@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
def puxar_responsabilidade_documento_provento(request):
    id_pendencia = request.GET['id_pendencia'].replace('.', '')
    # Verifica se id_pendencia contém apenas números
    if not id_pendencia.isdigit():
#         messages.error(request, u'Formato de pendência inválido')
        return HttpResponse(json.dumps({'resultado': False, 'mensagem': u'Formato de pendência inválido', 'responsavel': None, 'usuario_responsavel': False}), content_type = "application/json") 
    
#     pagina_atual = request.GET['pagina_atual']
#     request.session['pagina_atual_lista_pendencias'] = pagina_atual
    
    # Testa se pendência enviada existe
    try:
        pendencia = PendenciaDocumentoProvento.objects.get(id=id_pendencia)
    except PendenciaDocumentoProvento.DoesNotExist:
#         messages.error(request, u'A pendência enviada não existe')
        return HttpResponse(json.dumps({'resultado': False, 'mensagem': u'A pendência enviada não existe', 'responsavel': None, 'usuario_responsavel': False}), content_type = "application/json") 
    
    retorno, mensagem = alocar_pendencia_para_investidor(pendencia, request.user.investidor)
    # Carregar responsável
    responsavel = PendenciaDocumentoProvento.objects.get(id=id_pendencia).responsavel()
    # Definir responsável
    if responsavel != None:
        usuario_responsavel = True if responsavel.id == request.user.investidor.id else False
        responsavel = unicode(responsavel)
    else:
        usuario_responsavel = False
        
    if retorno:
        return HttpResponse(json.dumps({'resultado': retorno, 'mensagem': mensagem, 'responsavel': responsavel, 'usuario_responsavel': usuario_responsavel}), content_type = "application/json") 
    else:
        return HttpResponse(json.dumps({'resultado': retorno, 'mensagem': mensagem, 'responsavel': responsavel, 'usuario_responsavel': usuario_responsavel}), content_type = "application/json") 

@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
def remover_responsabilidade_documento_provento(request):
    id_pendencia = request.GET['id_pendencia'].replace('.', '')
    # Verifica se id_pendencia contém apenas números
    if not id_pendencia.isdigit():
#         messages.error(request, u'Formato de pendência inválido %s' % (id_pendencia))
        return HttpResponse(json.dumps({'resultado': False, 'mensagem': u'Formato de pendência inválido %s' % (id_pendencia)}), content_type = "application/json") 
    
#     pagina_atual = request.GET['pagina_atual']
#     request.session['pagina_atual_lista_pendencias'] = pagina_atual
    
    # Testa se pendência enviada existe
    try:
        pendencia = PendenciaDocumentoProvento.objects.get(id=id_pendencia)
    except PendenciaDocumentoProvento.DoesNotExist:
#         messages.error(request, u'A pendência enviada não existe')
        return HttpResponse(json.dumps({'resultado': False, 'mensagem': u'A pendência enviada não existe'}), content_type = "application/json") 
    
    retorno, mensagem = desalocar_pendencia_de_investidor(pendencia, request.user.investidor)
    # Carregar responsável
    responsavel = PendenciaDocumentoProvento.objects.get(id=id_pendencia).responsavel()
        
    if retorno:
        return HttpResponse(json.dumps({'resultado': retorno, 'mensagem': mensagem}), content_type = "application/json") 
    else:
        return HttpResponse(json.dumps({'resultado': retorno, 'mensagem': mensagem}), content_type = "application/json") 

@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
def validar_documento_provento(request, id_pendencia):
    pendencia = PendenciaDocumentoProvento.objects.get(id=id_pendencia)
    # Verificar se pendência é de leitura
    if pendencia.tipo != 'V':
        messages.success(request, 'Pendência não é de validação')
        return HttpResponseRedirect(reverse('listar_pendencias'))
    
    investidor = request.user.investidor
    
    if pendencia.documento.investidorleituradocumento.decisao == 'C':
        proventos_documento = ProventoAcaoDocumento.objects.filter(documento=pendencia.documento).values_list('descricao_provento', flat=True)
        descricoes_proventos = ProventoAcaoDescritoDocumentoBovespa.objects.filter(id__in=proventos_documento)
        
        # Descrição da decisão do responsável pela leitura
        pendencia.decisao = 'Criar %s proventos' % (ProventoAcaoDocumento.objects.filter(documento=pendencia.documento).count())
    elif pendencia.documento.investidorleituradocumento.decisao == 'E':
        descricoes_proventos = {}
        
        # Descrição da decisão do responsável pela leitura
        pendencia.decisao = 'Excluir documento'
    
    return TemplateResponse(request, 'gerador_proventos/validar_documento_provento.html', {'pendencia': pendencia, 'descricoes_proventos': descricoes_proventos})