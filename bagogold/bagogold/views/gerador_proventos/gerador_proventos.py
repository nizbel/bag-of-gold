# -*- coding: utf-8 -*-
from bagogold import settings
from bagogold.bagogold.forms.gerador_proventos import \
    ProventoAcaoDescritoDocumentoBovespaForm, \
    AcaoProventoAcaoDescritoDocumentoBovespaForm
from bagogold.bagogold.models.acoes import Acao, Provento
from bagogold.bagogold.models.empresa import Empresa
from bagogold.bagogold.models.gerador_proventos import DocumentoProventoBovespa, \
    PendenciaDocumentoProvento, ProventoAcaoDescritoDocumentoBovespa, \
    ProventoAcaoDocumento
from bagogold.bagogold.utils.gerador_proventos import \
    alocar_pendencia_para_investidor, desalocar_pendencia_de_investidor, \
    salvar_investidor_responsavel_por_leitura, criar_descricoes_provento_acoes, \
    desfazer_investidor_responsavel_por_leitura,  buscar_proventos_proximos_acao, \
    versionar_descricoes_relacionadas_acoes
from bagogold.bagogold.utils.investidores import is_superuser
from bagogold.bagogold.utils.misc import \
    formatar_zeros_a_direita_apos_2_casas_decimais
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test, \
    permission_required
from django.core.exceptions import ValidationError
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
                            desfazer_investidor_responsavel_por_leitura(pendencia, investidor)
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
        return HttpResponse(json.dumps({'resultado': False, 'mensagem': u'Formato de pendência inválido', 'responsavel': None, 'usuario_responsavel': False}), content_type = "application/json") 
    
    # Testa se pendência enviada existe
    try:
        pendencia = PendenciaDocumentoProvento.objects.get(id=id_pendencia)
    except PendenciaDocumentoProvento.DoesNotExist:
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
        return HttpResponse(json.dumps({'resultado': False, 'mensagem': u'Formato de pendência inválido %s' % (id_pendencia)}), content_type = "application/json") 
    
    # Testa se pendência enviada existe
    try:
        pendencia = PendenciaDocumentoProvento.objects.get(id=id_pendencia)
    except PendenciaDocumentoProvento.DoesNotExist:
        return HttpResponse(json.dumps({'resultado': False, 'mensagem': u'A pendência enviada não existe'}), content_type = "application/json") 
    
    retorno, mensagem = desalocar_pendencia_de_investidor(pendencia, request.user.investidor)
        
    if retorno:
        return HttpResponse(json.dumps({'resultado': retorno, 'mensagem': mensagem}), content_type = "application/json") 
    else:
        return HttpResponse(json.dumps({'resultado': retorno, 'mensagem': mensagem}), content_type = "application/json") 

@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
def validar_documento_provento(request, id_pendencia):
    pendencia = PendenciaDocumentoProvento.objects.get(id=id_pendencia)
    if request.method == 'POST':
        print request.POST
        # TODO testar validar
        if request.POST.get('validar'):
            if pendencia.documento.investidorleituradocumento.decisao == 'C':
                validacao_completa = True
                print 'Validar criação'
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
                        print 'Alterou', descricao.id
                        if request.POST.get('descricao_%s' % (descricao.id)):
                            # Verificar se foi relacionado a um provento ou a uma descrição
                            provento_relacionado = Provento.objects.get(id=request.POST.get('descricao_%s' % (descricao.id)))
                            print u'Descrição %s é relacionada a %s' % (descricao.id, provento_relacionado)
                            proventos_relacionados[descricao] = provento_relacionado
                        else:
                            validacao_completa = False
                            messages.error(request, 'Provento de identificador %s marcado como relacionado a outro provento, escolha um provento para a relação' % (descricao.id))
                            continue
                if validacao_completa:
                    print 'Validação completa'
                    # Salva versões alteradas para os provento_documentos
                    for descricao, provento in proventos_relacionados.items():
                        versionar_descricoes_relacionadas_acoes(descricao, provento)
                    # Altera proventos para serem oficiais
                    for provento_id in ProventoAcaoDocumento.objects.filter(documento=pendencia.documento).values_list('provento', flat=True):
                        provento = Provento.objects.get(id=provento_id)
                        if not provento.oficial_bovespa:
                            provento.oficial_bovespa = True
                            provento.save()
                            
            elif pendencia.documento.investidorleituradocumento.decisao == 'E':
                print 'Validar exclusão'
                # Apagar documento
                pendencia.documento.apagar_documento()
                
            # Salvar usuário responsável pela validação
            
            # Remover pendência
        
        # TODO testar recusar
        elif request.POST.get('recusar'):
            print 'Recusar'
        
    # Verificar se pendência é de validação
    if pendencia.tipo != 'V':
        messages.success(request, 'Pendência não é de validação')
        return HttpResponseRedirect(reverse('listar_pendencias'))
    
#     investidor = request.user.investidor
    
    if pendencia.documento.investidorleituradocumento.decisao == 'C':
        proventos_documento = ProventoAcaoDocumento.objects.filter(documento=pendencia.documento).values_list('descricao_provento', flat=True)
        descricoes_proventos = ProventoAcaoDescritoDocumentoBovespa.objects.filter(id__in=proventos_documento)
        for descricao_provento in descricoes_proventos:
            # Definir tipo de provento
            if descricao_provento.tipo_provento == 'A':
                descricao_provento.descricao_tipo_provento = u'Ações'
                descricao_provento.acoes_recebidas = descricao_provento.acaoproventoacaodescritodocumentobovespa_set.all()
                # Remover 0s a esquerda para valores
                for acao_descricao_provento in descricao_provento.acoes_recebidas:
                    acao_descricao_provento.valor_calculo_frac = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(acao_descricao_provento.valor_calculo_frac))
            elif descricao_provento.tipo_provento == 'D':
                descricao_provento.descricao_tipo_provento = u'Dividendos'
            elif descricao_provento.tipo_provento == 'J':
                descricao_provento.descricao_tipo_provento = u'JSCP'
            
            # Remover 0s a esquerda para valores
            descricao_provento.valor_unitario = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(descricao_provento.valor_unitario))
            
            # Buscar proventos próximos
            descricao_provento.proventos_proximos = buscar_proventos_proximos_acao(descricao_provento)
            for provento_proximo in descricao_provento.proventos_proximos:
                # Definir tipo de provento
                if provento_proximo.tipo_provento == 'A':
                    provento_proximo.descricao_tipo_provento = u'Ações'
                    provento_proximo.acoes_recebidas = provento_proximo.acaoprovento_set.all()
                    # Remover 0s a esquerda para valores
                    for acao_descricao_provento in provento_proximo.acoes_recebidas:
                        acao_descricao_provento.valor_calculo_frac = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(acao_descricao_provento.valor_calculo_frac))
                elif provento_proximo.tipo_provento == 'D':
                    provento_proximo.descricao_tipo_provento = u'Dividendos'
                elif provento_proximo.tipo_provento == 'J':
                    provento_proximo.descricao_tipo_provento = u'JSCP'
                
                # Remover 0s a esquerda para valores
                provento_proximo.valor_unitario = Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(provento_proximo.valor_unitario))
                        
        # Descrição da decisão do responsável pela leitura
        pendencia.decisao = 'Criar %s provento(s)' % (ProventoAcaoDocumento.objects.filter(documento=pendencia.documento).count())
    elif pendencia.documento.investidorleituradocumento.decisao == 'E':
        descricoes_proventos = {}
        
        # Descrição da decisão do responsável pela leitura
        pendencia.decisao = 'Excluir documento'
    
    return TemplateResponse(request, 'gerador_proventos/validar_documento_provento.html', {'pendencia': pendencia, 'descricoes_proventos': descricoes_proventos})