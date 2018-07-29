# -*- coding: utf-8 -*-
import re

css_novo = file('assets/layouts/layout3/css/layout.min.css', 'r').read()
css_antigo = file('assets/layouts/layout3/css/layout-original.min.css', 'r').read()

# Para minificado
lista_novo = re.findall('([^\{\}@]+)\{([^\{\}]*)\}', css_novo)
print len(lista_novo)
 
lista_antigo = re.findall('([^\{\}@]+)\{([^\{\}]*)\}', css_antigo)
print len(lista_antigo)

# Para nao-minificado
# lista_novo = [(re.sub('\/\*.*?\*\/', '', atr_novo_f[0]), re.sub('\/\*.*?\*\/', '', atr_novo_f[1]) ) for atr_novo_f in \
#               re.findall('([^\{\}]+)\{([^\{\}]*)\}', css_novo, re.DOTALL|re.MULTILINE)]
# print len(lista_novo)
#  
# lista_antigo = [(re.sub('\/\*.*?\*\/', '', atr_antigo_f[0]), re.sub('\/\*.*?\*\/', '', atr_antigo_f[1]) ) for atr_antigo_f in \
#                 re.findall('([^\{\}]+)\{([^\{\}]*)\}', css_antigo, re.DOTALL|re.MULTILINE)]
# print len(lista_antigo)

for atr_novo in lista_novo:
    removeu = False
    for atr_antigo in lista_antigo:
        if atr_novo[0] == atr_antigo[0]:
            # Verificar conteúdo
            if atr_novo[1] != atr_antigo[1]:
                print u'DIFERENÇA ENCONTRADA'
                print atr_novo
                print atr_antigo
            
            # Remover da lista
            lista_antigo.remove(atr_antigo)
            removeu = True
            break
    if not removeu:
        print u'não achou', atr_novo
        
print len(lista_antigo)