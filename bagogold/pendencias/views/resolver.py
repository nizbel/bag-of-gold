# -*- coding: utf-8 -*-
from bagogold.bagogold.models.td import OperacaoTitulo
from bagogold.bagogold.utils.td import \
    calcular_qtd_um_titulo_ate_dia_por_divisao
from bagogold.pendencias.models.pendencias import \
    PendenciaVencimentoTesouroDireto
from django.contrib.auth.decorators import login_required
from django.core.mail import mail_admins
from django.db import IntegrityError, transaction
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404
import datetime
import json
import traceback
from bagogold.bagogold.models.divisoes import DivisaoOperacaoTD

@login_required
def resolver_pendencia_vencimento_td(request):
    investidor = request.user.investidor
    # TODO achar um jeito melhor de testar pela pelo test_urls.py
    try:
        id_pendencia = int(request.GET.get('id_pendencia').replace('.', ''))
    except:
        return HttpResponse(json.dumps({'mensagem': u'Pendência inválida'}), content_type = "application/json") 
    pendencia = get_object_or_404(PendenciaVencimentoTesouroDireto, id=id_pendencia, investidor=investidor)
    
    if request.GET.get('confirmar'):
        try:
            with transaction.atomic():
                operacao = OperacaoTitulo(investidor=investidor, titulo=pendencia.titulo, quantidade=pendencia.quantidade, tipo_operacao='V', 
                                          preco_unitario=pendencia.titulo.valor_vencimento(), taxa_bvmf=0, taxa_custodia=0, 
                                          data=pendencia.titulo.data_vencimento, consolidada=True)
                operacao.save()
                for divisao_id, qtd in calcular_qtd_um_titulo_ate_dia_por_divisao(investidor, datetime.date.today(), pendencia.titulo.id).items():
                    divisao_operacao = DivisaoOperacaoTD(divisao_id=divisao_id, quantidade=qtd, operacao=operacao)
                    divisao_operacao.save()
                
        except IntegrityError as e:
            mail_admins(u'Erro na geração de venda para vencimento de Tesouro Direto', traceback.format_exc().decode('utf-8'))
            return HttpResponse(json.dumps({'resultado': False, 'mensagem': 'Erro na criação de operação de venda'}), content_type = "application/json")
        return HttpResponse(json.dumps({'resultado': True, 'mensagem': 'Operação de venda criada com sucesso', 'pendencia_id': pendencia.texto_id()}), content_type = "application/json")
        
    texto_modal = u'Confirmar venda:' \
        + u'<br>Título: <strong>%s</strong>' % (pendencia.titulo.nome()) \
        + u'<br>Quantidade: <strong>%s</strong>' % (str(pendencia.quantidade).replace('.', ',')) \
        + u'<br>Data: <strong>%s</strong>' % (pendencia.titulo.data_vencimento.strftime('%d/%m/%Y')) \
        + u'<br>Motivo: <strong>Vencimento</strong>'
    titulo_modal = 'Pendência de vencimento de título'
    
    return HttpResponse(json.dumps({'texto_modal': texto_modal, 'titulo_modal': titulo_modal}), content_type = "application/json") 
