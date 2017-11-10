# -*- coding: utf-8 -*-
from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.bagogold.models.gerador_proventos import \
    InvestidorResponsavelPendencia, InvestidorLeituraDocumento, \
    InvestidorValidacaoDocumento, PendenciaDocumentoProvento, \
    InvestidorRecusaDocumento, DocumentoProventoBovespa, ProventoFIIDocumento, \
    ProventoAcaoDocumento
from decimal import Decimal
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Permission, User
from django.db.models.aggregates import Count, Sum
from django.db.models.expressions import Case, When, F
from django.db.models.fields import BooleanField, DecimalField
from django.db.models.query_utils import Q
from django.template.response import TemplateResponse
from math import floor
import calendar
import datetime


@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
@adiciona_titulo_descricao('Detalhar pendências do usuário', 'Detalha informações sobre leituras, pendências, recusas e validações de um usuário do gerador de proventos')
def detalhar_pendencias_usuario(request, id_usuario):
    usuario = User.objects.get(id=id_usuario)
    
    usuario.pendencias_alocadas = PendenciaDocumentoProvento.objects.filter(investidorresponsavelpendencia__investidor=usuario.investidor)
    usuario.leituras = InvestidorLeituraDocumento.objects.filter(investidor=usuario.investidor)
    usuario.validacoes = InvestidorValidacaoDocumento.objects.filter(investidor=usuario.investidor)
    usuario.leituras_que_recusou = InvestidorRecusaDocumento.objects.filter(investidor=usuario.investidor)
    usuario.leituras_recusadas = InvestidorRecusaDocumento.objects.filter(responsavel_leitura=usuario.investidor)
    
    for pendencia in usuario.pendencias_alocadas:
        pendencia.tipo_pendencia = 'Leitura' if pendencia.tipo == 'L' else 'Validação'
    
    # Preparar gráficos de acompanhamento
    graf_leituras = list()
    graf_validacoes = list()
    graf_leituras_que_recusou = list()
    graf_leituras_recusadas = list()
    
    # Iterar mes a mes sobre a data de 2 anos atrás
    data_2_anos_atras = datetime.date.today().replace(day=1, year=datetime.date.today().year-2)
    while data_2_anos_atras <= datetime.date.today().replace(day=1):
        # Preparar data
        graf_leituras += [[str(calendar.timegm(data_2_anos_atras.replace(day=7).timetuple()) * 1000), usuario.leituras.filter(data_leitura__month=data_2_anos_atras.month, data_leitura__year=data_2_anos_atras.year).count()]]
        graf_validacoes += [[str(calendar.timegm(data_2_anos_atras.replace(day=13).timetuple()) * 1000), usuario.validacoes.filter(data_validacao__month=data_2_anos_atras.month, data_validacao__year=data_2_anos_atras.year).count()]]
        graf_leituras_que_recusou += [[str(calendar.timegm(data_2_anos_atras.replace(day=19).timetuple()) * 1000), usuario.leituras_que_recusou.filter(data_recusa__month=data_2_anos_atras.month, data_recusa__year=data_2_anos_atras.year).count()]]
        graf_leituras_recusadas += [[str(calendar.timegm(data_2_anos_atras.replace(day=25).timetuple()) * 1000), usuario.leituras_recusadas.filter(data_recusa__month=data_2_anos_atras.month, data_recusa__year=data_2_anos_atras.year).count()]]
        if data_2_anos_atras.month < 12:
            data_2_anos_atras = data_2_anos_atras.replace(month=data_2_anos_atras.month+1)
        else:
            data_2_anos_atras = data_2_anos_atras.replace(year=data_2_anos_atras.year+1, month=1)
            
    # Filtrar apenas últimas 200 para mostrar nas tabelas
    usuario.leituras = usuario.leituras.order_by('-data_leitura')[:200]
    usuario.validacoes = usuario.validacoes.order_by('-data_validacao')[:200]
    usuario.leituras_que_recusou = usuario.leituras_que_recusou.order_by('-data_recusa')[:200]
    usuario.leituras_recusadas = usuario.leituras_recusadas.order_by('-data_recusa')[:200]

    # Se usuário for do grupo da nova equipe de leituras, mostrar dados
    if usuario.groups.filter(name='Equipe de leitura').exists():
        # Tempo médio por exclusão: 51.43 Tempo médio por provento ação: 122.07 Tempo médio por provento fii: 79.4
        # Considerar leituras feitas a partir de 21/10/2017
        usuario.equipe_leitura = True
        
        leituras = InvestidorLeituraDocumento.objects.filter(data_leitura__gt=datetime.date(2017, 10, 21), investidor=usuario.investidor) \
            .annotate(validado=Case(When(documento__investidorvalidacaodocumento__isnull=False, then=True), # Anotar validação
                   default=False, output_field=BooleanField())) 
            
        # Separar leituras e adicionar tempos
        leituras_fii = leituras.filter(documento__tipo='F').annotate(proventos_criados=Count('documento__proventofiidocumento')) \
            .annotate(tempo=Case(When(decisao='C', then=(Decimal('79.4') * F('proventos_criados'))), 
                                 When(decisao='E', then=Decimal('51.43')), output_field=DecimalField()))
        leituras_acao = leituras.filter(documento__tipo='A').annotate(proventos_criados=Count('documento__proventoacaodocumento')) \
            .annotate(tempo=Case(When(decisao='C', then=(Decimal('122.07') * F('proventos_criados'))), 
                                 When(decisao='E', then=Decimal('51.43')), output_field=DecimalField()))
        
        # Totais
        qtd_acao_exclusao = leituras_acao.filter(decisao='E').count()
        qtd_acao_proventos = leituras_acao.filter(decisao='C').aggregate(total_proventos=Sum('proventos_criados'))['total_proventos'] or 0
        
        qtd_fii_exclusao = leituras_fii.filter(decisao='E').count()
        qtd_fii_proventos = leituras_fii.filter(decisao='C').aggregate(total_proventos=Sum('proventos_criados'))['total_proventos'] or 0
        
        # Validado
        qtd_acao_exclusao_validado = leituras_acao.filter(decisao='E', validado=True).count()
        qtd_acao_proventos_validado = leituras_acao.filter(decisao='C', validado=True).aggregate(total_proventos=Sum('proventos_criados'))['total_proventos'] or 0
        
        qtd_fii_exclusao_validado = leituras_fii.filter(decisao='E', validado=True).count()
        qtd_fii_proventos_validado = leituras_fii.filter(decisao='C', validado=True).aggregate(total_proventos=Sum('proventos_criados'))['total_proventos'] or 0
        
        tempo_total = Decimal((qtd_acao_exclusao + qtd_fii_exclusao) * Decimal('51.43') + qtd_acao_proventos * Decimal('122.07') \
                                      + qtd_fii_proventos * Decimal('79.4')) / 3600
        usuario.tempo_validado = Decimal((qtd_acao_exclusao_validado + qtd_fii_exclusao_validado) * Decimal('51.43') \
                                         + qtd_acao_proventos_validado * Decimal('122.07') + qtd_fii_proventos_validado * Decimal('79.4')) / 3600
        usuario.tempo_a_validar = tempo_total - usuario.tempo_validado
        
        # TODO usar novo modelo pagamento leitura
        valor_hora = PagamentoLeitura.VALOR_HORA
        usuario.pago = PagamentoLeitura.objects.filter(investidor=usuario.investidor).aggregate(total_pago=Sum('valor'))['total_pago'] or 0
        usuario.a_pagar = Decimal(floor(usuario.tempo_validado)) * valor_hora - usuario.pago
        
        # Parar popular a barra de acompanhamento
        usuario.progresso_tempo_total = tempo_total * valor_hora - usuario.pago
#         usuario.progresso_pago = usuario.pago
#         usuario.percentual_progresso_pago = usuario.progresso_pago / usuario.progresso_tempo_total * 100
        usuario.progresso_a_pagar = usuario.a_pagar
        usuario.percentual_progresso_a_pagar = usuario.progresso_a_pagar / usuario.progresso_tempo_total * 100
        usuario.progresso_validado = usuario.tempo_validado * valor_hora - usuario.a_pagar - usuario.pago
        usuario.percentual_progresso_validado = usuario.progresso_validado / usuario.progresso_tempo_total * 100
        
        # TODO Adicionar lista de pagamentos feitos

    return TemplateResponse(request, 'gerador_proventos/detalhar_pendencias_usuario.html', {'usuario': usuario, 'graf_leituras': graf_leituras, 'graf_validacoes': graf_validacoes,
                                                                                            'graf_leituras_que_recusou': graf_leituras_que_recusou, 'graf_leituras_recusadas': graf_leituras_recusadas})

@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
@adiciona_titulo_descricao('Listar usuários do gerador de proventos', 'Listagem de usuários com acesso ao gerador de proventos e dados sobre leituras/validações')
def listar_usuarios(request):
    permissao = Permission.objects.get(codename='pode_gerar_proventos')  
    usuarios = User.objects.filter(Q(user_permissions=permissao) | Q(is_superuser=True))
    
    for usuario in usuarios:
        usuario.pendencias_alocadas = InvestidorResponsavelPendencia.objects.filter(investidor=usuario.investidor).count()
        # Leituras
        usuario.leituras = InvestidorLeituraDocumento.objects.filter(investidor=usuario.investidor).count()
        if usuario.leituras == 0:
            usuario.taxa_leitura = 0
        else:
            data_leituras = len(list(set([data_hora.date() for data_hora in InvestidorLeituraDocumento.objects.filter(investidor=usuario.investidor) \
                                 .order_by('data_leitura').values_list('data_leitura', flat=True)])))
            usuario.taxa_leitura = Decimal(usuario.leituras) / max(data_leituras, 1)
        # Validações
        usuario.validacoes = InvestidorValidacaoDocumento.objects.filter(investidor=usuario.investidor).count()
        if usuario.validacoes == 0:
            usuario.taxa_validacao = 0
        else:
            data_validacoes = len(list(set([data_hora.date() for data_hora in InvestidorValidacaoDocumento.objects.filter(investidor=usuario.investidor) \
                                   .order_by('data_validacao').values_list('data_validacao', flat=True)])))
            usuario.taxa_validacao = Decimal(usuario.validacoes) / max(data_validacoes, 1)
    
    # Carregar estatísticas
    estatisticas = {}
    estatisticas['total_documentos'] = DocumentoProventoBovespa.objects.all().count()
    estatisticas['total_ref_30_dias'] = DocumentoProventoBovespa.objects.filter(data_referencia__gte=(datetime.date.today()-datetime.timedelta(days=30))).count()
    
    # Validados
    estatisticas['total_validado'] = estatisticas['total_documentos'] - PendenciaDocumentoProvento.objects.all().count()
    estatisticas['percentual_validado'] = 100 * Decimal(estatisticas['total_validado']) / estatisticas['total_documentos']
    estatisticas['percentual_validado_progress'] = str(estatisticas['percentual_validado']).replace(',', '.')
    estatisticas['percentual_validado_progress'] = estatisticas['percentual_validado_progress'][: min(len(estatisticas['percentual_validado_progress']),
                                                                                                      estatisticas['percentual_validado_progress'].find('.') + 4)]
    estatisticas['total_validado_usuario'] = InvestidorValidacaoDocumento.objects.filter(investidor__isnull=False).count()
    estatisticas['percentual_validado_usuario'] = 100 * Decimal(estatisticas['total_validado_usuario']) / estatisticas['total_validado']
    estatisticas['total_validado_sistema'] = estatisticas['total_validado'] - estatisticas['total_validado_usuario']
    estatisticas['percentual_validado_sistema'] = 100 * Decimal(estatisticas['total_validado_sistema']) / estatisticas['total_validado']
    data_primeira_validacao = InvestidorValidacaoDocumento.objects.all().order_by('data_validacao')[0].data_validacao.date()
    estatisticas['taxa_validacao_diaria'] =  Decimal(estatisticas['total_validado']) / (datetime.date.today() - data_primeira_validacao).days
    
    # Apenas lidos
    estatisticas['total_a_validar'] = PendenciaDocumentoProvento.objects.filter(tipo='V').count()
    estatisticas['percentual_a_validar'] = 100 * Decimal(estatisticas['total_a_validar']) / estatisticas['total_documentos']
    estatisticas['percentual_a_validar_progress'] = str(estatisticas['percentual_a_validar']).replace(',', '.')
    estatisticas['percentual_a_validar_progress'] = estatisticas['percentual_a_validar_progress'][: min(len(estatisticas['percentual_a_validar_progress']), 
                                                                                                        estatisticas['percentual_a_validar_progress'].find('.') + 4)]
    
    # Previsões
    estatisticas['previsao_total_documentos'] = estatisticas['total_documentos'] + estatisticas['total_ref_30_dias']
    estatisticas['previsao_total_validado'] = estatisticas['total_validado'] + int(30 *  estatisticas['taxa_validacao_diaria'])
    estatisticas['previsao_percentual_validado'] = 100 * Decimal(estatisticas['previsao_total_validado']) / estatisticas['previsao_total_documentos']
    estatisticas['previsao_percentual_validado_progress'] = str(estatisticas['previsao_percentual_validado']).replace(',', '.')
    estatisticas['previsao_percentual_validado_progress'] = estatisticas['previsao_percentual_validado_progress'][: min(len(estatisticas['previsao_percentual_validado_progress']),
                                                                                                      estatisticas['previsao_percentual_validado_progress'].find('.') + 4)]
    dias_para_validacao_completa = (estatisticas['total_documentos'] - estatisticas['total_validado'])/(estatisticas['taxa_validacao_diaria'] - Decimal(estatisticas['total_ref_30_dias'])/30)
    anos_validacao_completa = int(floor(dias_para_validacao_completa/365))
    dias_validacao_completa = int(floor(dias_para_validacao_completa % 365))
    horas_validacao_completa = int(floor((Decimal(dias_para_validacao_completa) - Decimal(floor(dias_para_validacao_completa))) * 24))
    estatisticas['previsao_tempo_validacao_completa'] = ''
    if anos_validacao_completa > 0:
        estatisticas['previsao_tempo_validacao_completa'] += '%s anos' % (anos_validacao_completa)
    if dias_validacao_completa > 0:
        estatisticas['previsao_tempo_validacao_completa'] += ', %s dias' % (dias_validacao_completa) if len(estatisticas['previsao_tempo_validacao_completa']) > 0 else \
            '%s dias' % (dias_validacao_completa)
    if horas_validacao_completa > 0:
        estatisticas['previsao_tempo_validacao_completa'] += ', %s horas' % (horas_validacao_completa) if len(estatisticas['previsao_tempo_validacao_completa']) > 0 else \
            '%s horas' % (horas_validacao_completa)
    
    return TemplateResponse(request, 'gerador_proventos/listar_usuarios.html', {'usuarios': usuarios, 'estatisticas': estatisticas})

