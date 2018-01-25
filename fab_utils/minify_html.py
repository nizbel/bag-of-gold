# -*- encoding: utf-8 -*-
from os import walk
import re

def minificar_html():
    arqs = []
    for (dirpath, _, arq_nomes) in walk('../bagogold/templates'):
        arqs.extend(['%s/%s' % (dirpath, arq_nome) for arq_nome in arq_nomes if arq_nome[-4:] == 'html'])
        
    for arq_nome in arqs:
        with open(arq_nome, 'r+') as arquivo:
            text = arquivo.read()
            text = re.sub('>\s+<', '> <', re.sub('\n\s+', ' ', re.sub('<!--[^\[\]]+?-->', '', text)))
            arquivo.seek(0)
            arquivo.write(text)
            arquivo.truncate()