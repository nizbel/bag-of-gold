# -*- coding: utf-8 -*-
from bagogold import settings
from bagogold.bagogold.models.utils import FuncionalidadeConstrucao
from django.template.response import TemplateResponse

def em_construcao(tag):
    def _dec(view_func):
        def _view(request, *args, **kwargs):
            if settings.ENV == 'DEV':
                if FuncionalidadeConstrucao.objects.filter(tag=tag).exists():
                    funcionalidade = FuncionalidadeConstrucao.objects.get(tag=tag)
                    percentual = funcionalidade.percentual
                    texto_construcao = u'<strong>%s</strong><br/>Em construção' % (funcionalidade.tag)
                else:
                    percentual = 0
                    texto_construcao = u'Página em construção'
                return TemplateResponse(request, 'construcao.html', {'percentual': percentual, 'texto_construcao': texto_construcao})
            else:
                return view_func(request, *args, **kwargs)
        return _view
    return _dec