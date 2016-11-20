# -*- coding: utf-8 -*-
from django.template.exceptions import TemplateDoesNotExist


class TesteNovaAparenciaMiddleWare(object): 
     
    def process_template_response(self, request, response):
        try:
            template_name_original = response.template_name
            response.template_name = ('teste/' + response.template_name) if request.session.get('testando_aparencia', False) else response.template_name
            response.render()
        except TemplateDoesNotExist:
            response.template_name = template_name_original
            response.render()
            
        return response
        