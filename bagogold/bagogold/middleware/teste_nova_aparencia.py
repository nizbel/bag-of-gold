# -*- coding: utf-8 -*-


class TesteNovaAparenciaMiddleWare(object): 
     
    def process_template_response(self, request, response):
        response.template_name = ('teste/' + response.template_name) if request.session.get('testando_aparencia', False) else response.template_name
        response.render()
        
        return response
        