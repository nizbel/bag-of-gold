# -*- coding: utf-8 -*-
from bagogold.pendencias.models.pendencias import \
    PendenciaVencimentoTesouroDireto
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
import json

@login_required
def resolver_pendencia_vencimento_td(request):
    investidor = request.user.investidor
    id_pendencia = int(request.GET['id_pendencia'])
    pendencia = get_object_or_404(PendenciaVencimentoTesouroDireto, id=id_pendencia, investidor=investidor)
    
    print request.GET.get('confirmar')
    
    if request.GET.get('confirmar'):
        print 'Criar'
        return HttpResponse(json.dumps({'resultado': True, 'mensagem': 'Operação de venda criada com sucesso'}), content_type = "application/json")
        
    texto_modal = u'Confirmar venda:' \
        + u'<br>Título: <strong>%s</strong>' % (pendencia.titulo.nome()) \
        + u'<br>Quantidade: <strong>%s</strong>' % (str(pendencia.quantidade).replace('.', ',')) \
        + u'<br>Data: <strong>%s</strong>' % (pendencia.titulo.data_vencimento.strftime('%d/%m/%Y')) \
        + u'<br>Motivo: <strong>Vencimento</strong>'
    titulo_modal = 'Pendência de vencimento de título'
    
    return HttpResponse(json.dumps({'texto_modal': texto_modal, 'titulo_modal': titulo_modal}), content_type = "application/json") 
