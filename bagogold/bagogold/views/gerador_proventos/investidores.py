# -*- coding: utf-8 -*-
from bagogold.bagogold.models.gerador_proventos import \
    InvestidorResponsavelPendencia, InvestidorLeituraDocumento, \
    InvestidorValidacaoDocumento, PendenciaDocumentoProvento, \
    InvestidorRecusaDocumento
from decimal import Decimal
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Permission, User
from django.db.models.query_utils import Q
from django.template.response import TemplateResponse
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
    
    return TemplateResponse(request, 'gerador_proventos/listar_usuarios.html', {'usuarios': usuarios})

