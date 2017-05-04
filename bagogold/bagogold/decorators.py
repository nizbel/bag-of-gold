# -*- coding: utf-8 -*-
from bagogold import settings
from django.template.response import TemplateResponse

def em_construcao(tag):
    def _dec(view_func):
        def _view(request, *args, **kwargs):
            if settings.ENV == 'DEV':
                
                percentual = 25
                return TemplateResponse(request, 'construcao.html', {'percentual': percentual})
    #                 percentual = FuncionalidadeConstrucao.objects.get(tag=tag).percentual
    #             else:
    #             if AplicacaoEmConstrucao.objects.filter(tag=tag):
            else:
                return view_func(request, *args, **kwargs)
        return _view
    return _dec