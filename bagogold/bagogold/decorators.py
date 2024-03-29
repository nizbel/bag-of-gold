# -*- coding: utf-8 -*-
from bagogold import settings
from bagogold.bagogold.models.utils import FuncionalidadeConstrucao
from django.template.response import TemplateResponse

def em_construcao(tag):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if settings.ENV != 'DEV':
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
        return wrapper
    return decorator

def adiciona_titulo_descricao(titulo, descricao):
    def decorator(view):
        def wrapper(request, *args, **kwargs):
            r = view(request, *args, **kwargs)
            # Verifica se é um TemplateResponse para ter contexto
            if isinstance(r, TemplateResponse):
                r.context_data['pagina_titulo'] = titulo
                r.context_data['pagina_descricao'] = descricao
                return r.render()
            else:
                return r
        return wrapper
    return decorator