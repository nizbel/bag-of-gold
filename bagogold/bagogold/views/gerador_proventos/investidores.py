# -*- coding: utf-8 -*-
from bagogold.bagogold.models.gerador_proventos import \
    InvestidorResponsavelPendencia, InvestidorLeituraDocumento, \
    InvestidorValidacaoDocumento, PendenciaDocumentoProvento,\
    InvestidorRecusaDocumento
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Permission, User
from django.db.models.query_utils import Q
from django.template.response import TemplateResponse
import calendar
import datetime


@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
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
    
    # Iterar mes a mes sobre a data de 2 anos atrás
    data_2_anos_atras = datetime.date.today().replace(day=1, year=datetime.date.today().year-2)
    while data_2_anos_atras <= datetime.date.today().replace(day=1):
        # Preparar data
        graf_leituras += [[str(calendar.timegm(data_2_anos_atras.replace(day=7).timetuple()) * 1000), usuario.leituras.filter(data_leitura__month=data_2_anos_atras.month, data_leitura__year=data_2_anos_atras.year).count()]]
        graf_validacoes += [[str(calendar.timegm(data_2_anos_atras.replace(day=13).timetuple()) * 1000), usuario.validacoes.filter(data_validacao__month=data_2_anos_atras.month, data_validacao__year=data_2_anos_atras.year).count()]]
        graf_leituras_que_recusou = [[str(calendar.timegm(data_2_anos_atras.replace(day=19).timetuple()) * 1000), usuario.leituras_que_recusou.filter(data_recusa__month=data_2_anos_atras.month, data_recusa__year=data_2_anos_atras.year).count()]]
        graf_leituras_recusadas = [[str(calendar.timegm(data_2_anos_atras.replace(day=25).timetuple()) * 1000), usuario.leituras_recusadas.filter(data_recusa__month=data_2_anos_atras.month, data_recusa__year=data_2_anos_atras.year).count()]]
        if data_2_anos_atras.month < 12:
            data_2_anos_atras = data_2_anos_atras.replace(month=data_2_anos_atras.month+1)
        else:
            data_2_anos_atras = data_2_anos_atras.replace(year=data_2_anos_atras.year+1, month=1)
    return TemplateResponse(request, 'gerador_proventos/detalhar_pendencias_usuario.html', {'usuario': usuario, 'graf_leituras': graf_leituras, 'graf_validacoes': graf_validacoes,
                                                                                            'graf_leituras_que_recusou': graf_leituras_que_recusou, 'graf_leituras_recusadas': graf_leituras_recusadas})

@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
def listar_usuarios(request):
    permissao = Permission.objects.get(codename='pode_gerar_proventos')  
    usuarios = User.objects.filter(Q(user_permissions=permissao) | Q(is_superuser=True))
    
    for usuario in usuarios:
        usuario.pendencias_alocadas = InvestidorResponsavelPendencia.objects.filter(investidor=usuario.investidor).count()
        usuario.leituras = InvestidorLeituraDocumento.objects.filter(investidor=usuario.investidor).count()
        usuario.validacoes = InvestidorValidacaoDocumento.objects.filter(investidor=usuario.investidor).count()
    
    return TemplateResponse(request, 'gerador_proventos/listar_usuarios.html', {'usuarios': usuarios})

