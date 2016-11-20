# -*- coding: utf-8 -*-
from bagogold.bagogold.models.gerador_proventos import \
    InvestidorResponsavelPendencia, InvestidorLeituraDocumento, \
    InvestidorValidacaoDocumento
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Permission, User
from django.template.response import TemplateResponse

@login_required
@permission_required('bagogold.pode_gerar_proventos', raise_exception=True)
def listar_usuarios(request):
    
    permissao = Permission.objects.get(codename='pode_gerar_proventos')  
    usuarios = User.objects.filter(user_permissions=permissao)
    
    for usuario in usuarios:
        usuario.pendencias_alocadas = InvestidorResponsavelPendencia.objects.filter(investidor=usuario.investidor)
        usuario.leituras = InvestidorLeituraDocumento.objects.filter(investidor=usuario.investidor)
        usuario.validacoes = InvestidorValidacaoDocumento.objects.filter(investidor=usuario.investidor)
    
    return TemplateResponse(request, 'gerador_proventos/listar_usuarios.html', {'usuarios': usuarios})

