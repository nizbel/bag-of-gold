# -*- coding: utf-8 -*-
from bagogold.bagogold.utils.investidores import is_superuser
from django.contrib.auth.decorators import login_required, user_passes_test


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
    pass


@login_required
@user_passes_test(is_superuser)
def listar_pendencias(request):
    pass