# -*- coding: utf-8 -*-
import calendar
import datetime
from decimal import Decimal
import itertools
from math import floor

from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Permission, User
from django.db.models.aggregates import Count, Sum
from django.db.models.expressions import Case, When, F, Value
from django.db.models.fields import BooleanField, DecimalField, CharField
from django.db.models.query_utils import Q
from django.template.response import TemplateResponse

from bagogold.bagogold.decorators import adiciona_titulo_descricao
from bagogold.bagogold.models.acoes import Acao
from bagogold.bagogold.models.gerador_proventos import \
    InvestidorResponsavelPendencia, InvestidorLeituraDocumento, \
    InvestidorValidacaoDocumento, PendenciaDocumentoProvento, \
    InvestidorRecusaDocumento, DocumentoProventoBovespa, PagamentoLeitura, \
    HistoricoInvestidorLeituraDocumento, HistoricoInvestidorValidacaoDocumento, \
    HistoricoInvestidorRecusaDocumento

@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
@adiciona_titulo_descricao('Detalhar pendências do usuário', 'Detalha informações sobre leituras, pendências, recusas e validações de um usuário do gerador de proventos')
def central_pagamentos(request, id_usuario):
    pass

@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
@adiciona_titulo_descricao('Detalhar pendências do usuário', 'Detalha informações sobre leituras, pendências, recusas e validações de um usuário do gerador de proventos')
def detalhar_pendencias_usuario(request, id_usuario):
    usuario = User.objects.get(id=id_usuario)
    
    usuario.pendencias_alocadas = PendenciaDocumentoProvento.objects.filter(investidorresponsavelpendencia__investidor=usuario.investidor) \
        .annotate(tipo_pendencia=Case(When(tipo='L', then=Value(u'Leitura')), When(tipo='V', then=Value(u'Validação')), output_field=CharField())) \
        .select_related('investidorresponsavelpendencia', 'documento', 'documento__empresa')
    usuario.leituras = InvestidorLeituraDocumento.objects.filter(investidor=usuario.investidor).select_related('documento', 'documento__empresa')
    usuario.historico_leituras = HistoricoInvestidorLeituraDocumento.objects.filter(investidor=usuario.investidor)
    usuario.validacoes = InvestidorValidacaoDocumento.objects.filter(investidor=usuario.investidor).select_related('documento', 'documento__empresa')
    usuario.historico_validacoes = HistoricoInvestidorValidacaoDocumento.objects.filter(investidor=usuario.investidor)
    usuario.leituras_que_recusou = InvestidorRecusaDocumento.objects.filter(investidor=usuario.investidor).select_related('documento', 'documento__empresa')
    usuario.historico_leituras_que_recusou = HistoricoInvestidorRecusaDocumento.objects.filter(investidor=usuario.investidor)
    usuario.leituras_recusadas = InvestidorRecusaDocumento.objects.filter(responsavel_leitura=usuario.investidor).select_related('documento', 'documento__empresa')
    usuario.historico_leituras_recusadas = HistoricoInvestidorRecusaDocumento.objects.filter(responsavel_leitura=usuario.investidor)
    
    # Preparar gráficos de acompanhamento
    graf_leituras = list()
    graf_validacoes = list()
    graf_leituras_que_recusou = list()
    graf_leituras_recusadas = list()
    
    # Iterar mes a mes sobre a data de 2 anos atrás
    data_2_anos_atras = datetime.date.today().replace(day=1, year=datetime.date.today().year-2)
    while data_2_anos_atras <= datetime.date.today().replace(day=1):
        # Preparar data
        graf_leituras += [[str(calendar.timegm(data_2_anos_atras.replace(day=7).timetuple()) * 1000), 
                           len([leitura for leitura in usuario.leituras if leitura.data_leitura.month == data_2_anos_atras.month \
                                and leitura.data_leitura.year == data_2_anos_atras.year]) \
                           + len([historico_leitura for historico_leitura in usuario.historico_leituras if historico_leitura.data_leitura.month == data_2_anos_atras.month \
                                and historico_leitura.data_leitura.year == data_2_anos_atras.year])]]
        graf_validacoes += [[str(calendar.timegm(data_2_anos_atras.replace(day=13).timetuple()) * 1000), 
                             len([validacao for validacao in usuario.validacoes if validacao.data_validacao.month == data_2_anos_atras.month \
                                  and validacao.data_validacao.year == data_2_anos_atras.year]) \
                             + len([historico_validacao for historico_validacao in usuario.historico_validacoes if historico_validacao.data_validacao.month == data_2_anos_atras.month \
                                  and historico_validacao.data_validacao.year == data_2_anos_atras.year])]]
        graf_leituras_que_recusou += [[str(calendar.timegm(data_2_anos_atras.replace(day=19).timetuple()) * 1000), 
                                   len([recusa for recusa in usuario.leituras_que_recusou if recusa.data_recusa.month == data_2_anos_atras.month \
                                        and recusa.data_recusa.year == data_2_anos_atras.year]) \
                                   + len([historico_recusa for historico_recusa in usuario.historico_leituras_que_recusou if historico_recusa.data_recusa.month == data_2_anos_atras.month \
                                        and historico_recusa.data_recusa.year == data_2_anos_atras.year])]]
#                                        usuario.leituras_que_recusou.filter(data_recusa__month=data_2_anos_atras.month, data_recusa__year=data_2_anos_atras.year).count() \
#                                        + usuario.historico_leituras_que_recusou.filter(data_recusa__month=data_2_anos_atras.month, data_recusa__year=data_2_anos_atras.year).count()]]
        graf_leituras_recusadas += [[str(calendar.timegm(data_2_anos_atras.replace(day=25).timetuple()) * 1000), 
                                   len([recusada for recusada in usuario.leituras_recusadas if recusada.data_recusa.month == data_2_anos_atras.month \
                                        and recusada.data_recusa.year == data_2_anos_atras.year]) \
                                   + len([historico_recusada for historico_recusada in usuario.historico_leituras_recusadas if historico_recusada.data_recusa.month == data_2_anos_atras.month \
                                        and historico_recusada.data_recusa.year == data_2_anos_atras.year])]]
#                                      usuario.leituras_recusadas.filter(data_recusa__month=data_2_anos_atras.month, data_recusa__year=data_2_anos_atras.year).count() \
#                                      + usuario.historico_leituras_recusadas.filter(data_recusa__month=data_2_anos_atras.month, data_recusa__year=data_2_anos_atras.year).count()]]
        if data_2_anos_atras.month < 12:
            data_2_anos_atras = data_2_anos_atras.replace(month=data_2_anos_atras.month+1)
        else:
            data_2_anos_atras = data_2_anos_atras.replace(year=data_2_anos_atras.year+1, month=1)
            
    # Filtrar apenas últimas 200 para mostrar nas tabelas
    usuario.leituras = usuario.leituras.order_by('-data_leitura')[:200]
    usuario.validacoes = usuario.validacoes.order_by('-data_validacao')[:200]
    usuario.leituras_que_recusou = usuario.leituras_que_recusou.order_by('-data_recusa')[:200]
    usuario.leituras_recusadas = usuario.leituras_recusadas.order_by('-data_recusa')[:200]
    
    # Buscar ticker de ações para preencher nome de documento
    ticker_acoes = Acao.objects.all().order_by('empresa').values('empresa').values_list('empresa', 'ticker')
     
    for item in itertools.chain(usuario.leituras, usuario.validacoes, usuario.pendencias_alocadas, usuario.leituras_que_recusou, usuario.leituras_recusadas):
        # Preencher ticker de empresa
        if item.documento.empresa.codigo_cvm == None or any([char.isdigit() for char in item.documento.empresa.codigo_cvm]):
            for empresa_id, ticker in ticker_acoes:
                if item.documento.empresa.id == empresa_id:
                    item.documento.nome = u'%s-%s' % (''.join(char for char in ticker if not char.isdigit()), item.documento.protocolo)
                    break
        else:
            item.documento.nome = u'%s-%s' % (item.documento.empresa.codigo_cvm, item.documento.protocolo)

    # Se usuário for do grupo da nova equipe de leituras, mostrar dados
    if usuario.groups.filter(name='Equipe de leitura').exists():
        # Tempo médio por exclusão: 51.43 Tempo médio por provento ação: 122.07 Tempo médio por provento fii: 79.4
        # Considerar leituras feitas a partir de 21/10/2017
        # TODO a partir de 21/09/2018, aumentar valor da hora para 30 reais
        usuario.equipe_leitura = True
        
        leituras = InvestidorLeituraDocumento.objects.filter(data_leitura__gt=datetime.date(2017, 10, 21), investidor=usuario.investidor) \
            .annotate(validado=Case(When(documento__investidorvalidacaodocumento__isnull=False, then=True), # Anotar validação
                   default=False, output_field=BooleanField())) 
        
        # Guarda leituras apagadas
        historico_leituras = HistoricoInvestidorLeituraDocumento.objects.filter(data_leitura__gt=datetime.date(2017, 10, 21), investidor=usuario.investidor)
            
        # Separar leituras e adicionar tempos
        leituras_fii = leituras.filter(documento__tipo='F').annotate(proventos_criados=Count('documento__proventofiidocumento')) \
            .annotate(tempo=Case(When(decisao='C', then=(PagamentoLeitura.TEMPO_LEITURA_PROVENTO_FII * F('proventos_criados'))), 
                                 When(decisao='E', then=PagamentoLeitura.TEMPO_EXCLUSAO_DOCUMENTO), output_field=DecimalField())) \
            .annotate(valor_pagamento=Case(When(data_leitura__gte=datetime.date(2018, 9, 21), then=Value(Decimal(30))),
                                           When(data_leitura__lt=datetime.date(2018, 9, 21), then=Value(Decimal(25))), output_field=DecimalField())) \
            .values('tempo', 'valor_pagamento', 'data_leitura')
        leituras_acao = leituras.filter(documento__tipo='A').annotate(proventos_criados=Count('documento__proventoacaodocumento')) \
            .annotate(tempo=Case(When(decisao='C', then=(PagamentoLeitura.TEMPO_LEITURA_PROVENTO_ACAO * F('proventos_criados'))), 
                                 When(decisao='E', then=PagamentoLeitura.TEMPO_EXCLUSAO_DOCUMENTO), output_field=DecimalField())) \
            .annotate(valor_pagamento=Case(When(data_leitura__gte=datetime.date(2018, 9, 21), then=Value(Decimal(30))),
                                           When(data_leitura__lt=datetime.date(2018, 9, 21), then=Value(Decimal(25))), output_field=DecimalField())) \
            .values('tempo', 'valor_pagamento', 'data_leitura')
            
        # Separar de leituras apagadas
        historico_leituras_fii = historico_leituras.filter(tipo_investimento='F') \
            .annotate(tempo=Case(When(decisao='C', then=(PagamentoLeitura.TEMPO_LEITURA_PROVENTO_FII * F('proventos_criados'))), 
                                 When(decisao='E', then=PagamentoLeitura.TEMPO_EXCLUSAO_DOCUMENTO), output_field=DecimalField())) \
            .annotate(valor_pagamento=Case(When(data_leitura__gte=datetime.date(2018, 9, 21), then=Value(Decimal(30))),
                                           When(data_leitura__lt=datetime.date(2018, 9, 21), then=Value(Decimal(25))), output_field=DecimalField())) \
            .values('tempo', 'valor_pagamento', 'data_leitura')
        historico_leituras_acao = historico_leituras.filter(tipo_investimento='A') \
            .annotate(tempo=Case(When(decisao='C', then=(PagamentoLeitura.TEMPO_LEITURA_PROVENTO_ACAO * F('proventos_criados'))), 
                                 When(decisao='E', then=PagamentoLeitura.TEMPO_EXCLUSAO_DOCUMENTO), output_field=DecimalField())) \
            .annotate(valor_pagamento=Case(When(data_leitura__gte=datetime.date(2018, 9, 21), then=Value(Decimal(30))),
                                           When(data_leitura__lt=datetime.date(2018, 9, 21), then=Value(Decimal(25))), output_field=DecimalField())) \
            .values('tempo', 'valor_pagamento', 'data_leitura')
        
        # Totais
#         qtd_acao_exclusao = leituras_acao.filter(decisao='E').count() + historico_leituras_acao.filter(decisao='E').count()
#         qtd_acao_proventos = (leituras_acao.filter(decisao='C').aggregate(total_proventos=Sum('proventos_criados'))['total_proventos'] or 0) \
#             + (historico_leituras_acao.filter(decisao='C').aggregate(total_proventos=Sum('proventos_criados'))['total_proventos'] or 0)
#         
#         qtd_fii_exclusao = leituras_fii.filter(decisao='E').count() + historico_leituras_fii.filter(decisao='E').count()
#         qtd_fii_proventos = (leituras_fii.filter(decisao='C').aggregate(total_proventos=Sum('proventos_criados'))['total_proventos'] or 0) \
#             + (historico_leituras_fii.filter(decisao='C').aggregate(total_proventos=Sum('proventos_criados'))['total_proventos'] or 0)
        
        # Validado
        # Históricos de leitura contam como validados sempre
#         qtd_acao_exclusao_validado = leituras_acao.filter(decisao='E', validado=True).count() + historico_leituras_acao.filter(decisao='E').count()
#         qtd_acao_proventos_validado = (leituras_acao.filter(decisao='C', validado=True).aggregate(total_proventos=Sum('proventos_criados'))['total_proventos'] or 0) \
#             + (historico_leituras_acao.filter(decisao='C').aggregate(total_proventos=Sum('proventos_criados'))['total_proventos'] or 0)
#         
#         qtd_fii_exclusao_validado = leituras_fii.filter(decisao='E', validado=True).count() + historico_leituras_fii.filter(decisao='E').count()
#         qtd_fii_proventos_validado = (leituras_fii.filter(decisao='C', validado=True).aggregate(total_proventos=Sum('proventos_criados'))['total_proventos'] or 0) \
#             + (historico_leituras_fii.filter(decisao='C').aggregate(total_proventos=Sum('proventos_criados'))['total_proventos'] or 0)
        
#         tempo_total = Decimal((qtd_acao_exclusao + qtd_fii_exclusao) * PagamentoLeitura.TEMPO_EXCLUSAO_DOCUMENTO + qtd_acao_proventos * PagamentoLeitura.TEMPO_LEITURA_PROVENTO_ACAO \
#                                       + qtd_fii_proventos * PagamentoLeitura.TEMPO_LEITURA_PROVENTO_FII) / 3600
        tempo_total = Decimal(sum([leitura['tempo'] for leitura in leituras_acao] + [leitura['tempo'] for leitura in leituras_fii] + [historico_leitura['tempo'] for historico_leitura in historico_leituras_acao] \
                                  + [historico_leitura['tempo'] for historico_leitura in historico_leituras_fii])) / 3600
        
        # Calcular quanto deve ser recebido por todas as leituras feitas
        pagamento_total = Decimal(sum([leitura['tempo'] * leitura['valor_pagamento'] for leitura in leituras_acao] \
                                      + [leitura['tempo'] * leitura['valor_pagamento'] for leitura in leituras_fii] \
                                      + [historico_leitura['tempo'] * historico_leitura['valor_pagamento'] for historico_leitura in historico_leituras_acao] \
                                      + [historico_leitura['tempo'] * historico_leitura['valor_pagamento'] for historico_leitura in historico_leituras_fii])) / 3600
#         usuario['tempo']_validado = Decimal((qtd_acao_exclusao_validado + qtd_fii_exclusao_validado) * PagamentoLeitura['tempo']_EXCLUSAO_DOCUMENTO \
#                                          + qtd_acao_proventos_validado * PagamentoLeitura['tempo']_LEITURA_PROVENTO_ACAO + qtd_fii_proventos_validado * PagamentoLeitura['tempo']_LEITURA_PROVENTO_FII) / 3600
        # Tempo e pagamento validados
        usuario.tempo_validado = Decimal(sum([leitura['tempo'] for leitura in leituras_acao.filter(validado=True)] + [leitura['tempo'] for leitura in leituras_fii.filter(validado=True)] \
                                             + [historico_leitura['tempo'] for historico_leitura in historico_leituras_acao] \
                                             + [historico_leitura['tempo'] for historico_leitura in historico_leituras_fii])) / 3600
        usuario.pagamento_validado = Decimal(sum([leitura['tempo'] * leitura['valor_pagamento'] for leitura in leituras_acao.filter(validado=True)] \
                                                 + [leitura['tempo'] * leitura['valor_pagamento'] for leitura in leituras_fii.filter(validado=True)] \
                                                 + [historico_leitura['tempo'] * historico_leitura['valor_pagamento'] for historico_leitura in historico_leituras_acao] \
                                                 + [historico_leitura['tempo'] * historico_leitura['valor_pagamento'] for historico_leitura in historico_leituras_fii])) / 3600
        # Tempo e pagamento a validar
        usuario.tempo_a_validar = tempo_total - usuario.tempo_validado
        usuario.pagto_tempo_a_validar = (pagamento_total - usuario.pagamento_validado).quantize(Decimal('0.01'))
#         usuario.pagto_tempo_a_validar = (usuario.tempo_a_validar * PagamentoLeitura.VALOR_HORA).quantize(Decimal('0.01'))
        
        # Usar novo modelo pagamento leitura
#         valor_hora = PagamentoLeitura.VALOR_HORA
        usuario.pago = PagamentoLeitura.objects.filter(investidor=usuario.investidor).aggregate(total_pago=Sum('valor'))['total_pago'] or 0
        # Valor a pagar deve ser 0 para casos em que pagamentos foram feitos antes das validações
        
        usuario.a_pagar = max(Decimal(floor(usuario.pagamento_validado)) - usuario.pago, 0)
        
        # Parar popular a barra de acompanhamento
        # Tempo total deve ser 1 para casos em que pagamentos foram feitos antes das validações, excedendo tempo
        usuario.progresso_tempo_total = max(pagamento_total - usuario.pago, 1)
#         usuario.progresso_pago = usuario.pago
#         usuario.percentual_progresso_pago = usuario.progresso_pago / usuario.progresso_tempo_total * 100
        usuario.progresso_a_pagar = usuario.a_pagar
        usuario.percentual_progresso_a_pagar = usuario.progresso_a_pagar / usuario.progresso_tempo_total * 100
        # Tempo validado deve ser 0 para casos em que pagamentos foram feitos antes das validações, excedendo tempo
        usuario.progresso_validado = max(usuario.pagamento_validado - usuario.a_pagar - usuario.pago, 0)
        usuario.percentual_progresso_validado = usuario.progresso_validado / usuario.progresso_tempo_total * 100
        
        # Adicionar lista de pagamentos feitos
        usuario.pagamentos = PagamentoLeitura.objects.filter(investidor=usuario.investidor)

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
        usuario.leituras = InvestidorLeituraDocumento.objects.filter(investidor=usuario.investidor).count() \
            + HistoricoInvestidorLeituraDocumento.objects.filter(investidor=usuario.investidor).count()
        if usuario.leituras == 0:
            usuario.taxa_leitura = 0
        else:
            data_leituras = len(list(set([data_hora.date() for data_hora in InvestidorLeituraDocumento.objects.filter(investidor=usuario.investidor) \
                                 .order_by('data_leitura').values_list('data_leitura', flat=True)])))
            usuario.taxa_leitura = Decimal(usuario.leituras) / max(data_leituras, 1)
        # Validações
        usuario.validacoes = InvestidorValidacaoDocumento.objects.filter(investidor=usuario.investidor).count() \
            + HistoricoInvestidorValidacaoDocumento.objects.filter(investidor=usuario.investidor).count()
        if usuario.validacoes == 0:
            usuario.taxa_validacao = 0
        else:
            data_validacoes = len(list(set([data_hora.date() for data_hora in InvestidorValidacaoDocumento.objects.filter(investidor=usuario.investidor) \
                                   .order_by('data_validacao').values_list('data_validacao', flat=True)])))
            usuario.taxa_validacao = Decimal(usuario.validacoes) / max(data_validacoes, 1)
    
    # Carregar estatísticas
    estatisticas = {}
    estatisticas['total_documentos'] = DocumentoProventoBovespa.objects.all().count()
    estatisticas['total_ref_30_dias'] = DocumentoProventoBovespa.objects.filter(data_referencia__gte=(datetime.date.today() - datetime.timedelta(days=30))).count()
    
    # Validados
    estatisticas['total_validado'] = estatisticas['total_documentos'] - PendenciaDocumentoProvento.objects.all().count()
    estatisticas['percentual_validado'] = 100 * Decimal(estatisticas['total_validado']) / (estatisticas['total_documentos'] or 1)
    estatisticas['percentual_validado_progress'] = str(estatisticas['percentual_validado']).replace(',', '.')
    estatisticas['percentual_validado_progress'] = estatisticas['percentual_validado_progress'][: min(len(estatisticas['percentual_validado_progress']),
                                                                                                      estatisticas['percentual_validado_progress'].find('.') + 4)]
    estatisticas['total_validado_usuario'] = InvestidorValidacaoDocumento.objects.filter(investidor__isnull=False).count()
    estatisticas['percentual_validado_usuario'] = 100 * Decimal(estatisticas['total_validado_usuario']) / (estatisticas['total_validado'] or 1)
    estatisticas['total_validado_sistema'] = estatisticas['total_validado'] - estatisticas['total_validado_usuario']
    estatisticas['percentual_validado_sistema'] = 100 * Decimal(estatisticas['total_validado_sistema']) / (estatisticas['total_validado'] or 1)
#     if InvestidorValidacaoDocumento.objects.exists():
#         data_primeira_validacao = InvestidorValidacaoDocumento.objects.all().order_by('data_validacao')[0].data_validacao.date()
#     else:
#         data_primeira_validacao = datetime.date.today()
#     estatisticas['validacoes_30_dias'] =  Decimal(estatisticas['total_validado']) / ((datetime.date.today() - data_primeira_validacao).days or 1)
    # Soma as validações dos últimas 30 dias feitas pelo sistema e feitos por usuários
    estatisticas['validacoes_30_dias'] =  estatisticas['total_ref_30_dias'] \
        - PendenciaDocumentoProvento.objects.filter(documento__data_referencia__gte=(datetime.date.today() - datetime.timedelta(days=30))).count() \
        - InvestidorValidacaoDocumento.objects.filter(documento__data_referencia__gte=(datetime.date.today() - datetime.timedelta(days=30))).count() \
        + InvestidorValidacaoDocumento.objects.filter(data_validacao__gte=(datetime.date.today() - datetime.timedelta(days=30))).count()
    
    # Apenas lidos
    estatisticas['total_a_validar'] = PendenciaDocumentoProvento.objects.filter(tipo='V').count()
    estatisticas['percentual_a_validar'] = 100 * Decimal(estatisticas['total_a_validar']) / (estatisticas['total_documentos'] or 1)
    estatisticas['percentual_a_validar_progress'] = str(estatisticas['percentual_a_validar']).replace(',', '.')
    estatisticas['percentual_a_validar_progress'] = estatisticas['percentual_a_validar_progress'][: min(len(estatisticas['percentual_a_validar_progress']), 
                                                                                                        estatisticas['percentual_a_validar_progress'].find('.') + 4)]
    
    # Previsões
    estatisticas['previsao_total_documentos'] = estatisticas['total_documentos'] + estatisticas['total_ref_30_dias']
    estatisticas['previsao_total_validado'] = estatisticas['total_validado'] + estatisticas['validacoes_30_dias']
    estatisticas['previsao_percentual_validado'] = 100 * Decimal(estatisticas['previsao_total_validado']) / (estatisticas['previsao_total_documentos'] or 1)
    estatisticas['previsao_percentual_validado_progress'] = str(estatisticas['previsao_percentual_validado']).replace(',', '.')
    estatisticas['previsao_percentual_validado_progress'] = estatisticas['previsao_percentual_validado_progress'][: min(len(estatisticas['previsao_percentual_validado_progress']),
                                                                                                      estatisticas['previsao_percentual_validado_progress'].find('.') + 4)]
    
    # Verifica se taxa validações está maior que taxa de geração de documentos
    if estatisticas['validacoes_30_dias'] > estatisticas['total_ref_30_dias']:
        dias_para_validacao_completa = (estatisticas['total_documentos'] - estatisticas['total_validado'])/ \
            (Decimal(estatisticas['validacoes_30_dias'] - estatisticas['total_ref_30_dias']) / 1)
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
    else:
        estatisticas['previsao_tempo_validacao_completa'] = 'Indefinido'
    
    return TemplateResponse(request, 'gerador_proventos/listar_usuarios.html', {'usuarios': usuarios, 'estatisticas': estatisticas})

