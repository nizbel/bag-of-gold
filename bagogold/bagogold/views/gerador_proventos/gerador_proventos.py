# -*- coding: utf-8 -*-
from bagogold.bagogold.utils.investidores import is_superuser
from django.contrib.auth.decorators import login_required, user_passes_test
from bagogold.bagogold.models.gerador_proventos import DocumentoBovespa


@login_required
@user_passes_test(is_superuser)
def listar_proventos(request):
    pass


@login_required
@user_passes_test(is_superuser)
def inserir_provento(request):
    pass


@login_required
@user_passes_test(is_superuser)
def listar_documentos(request):
    documentos = DocumentoBovespa.objects.all()
    
    for documento in documentos:
        # Preparar o valor mais atual para carência
        historico_carencia = HistoricoCarenciaLetraCredito.objects.filter(letra_credito=lc).exclude(data=None).order_by('-data')
        if historico_carencia:
            lc.carencia_atual = historico_carencia[0].carencia
        else:
            lc.carencia_atual = HistoricoCarenciaLetraCredito.objects.get(letra_credito=lc).carencia
        # Preparar o valor mais atual de rendimento
        historico_rendimento = HistoricoPorcentagemLetraCredito.objects.filter(letra_credito=lc).exclude(data=None).order_by('-data')
#         print historico_rendimento
        if historico_rendimento:
            lc.rendimento_atual = historico_rendimento[0].porcentagem_di
        else:
            lc.rendimento_atual = HistoricoPorcentagemLetraCredito.objects.get(letra_credito=lc).porcentagem_di

    return render_to_response('lc/listar_lc.html', {'lcs': lcs},
                              context_instance=RequestContext(request))

@login_required
@user_passes_test(is_superuser)
def listar_pendencias(request):
    pass