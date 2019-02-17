#!/home/nizbel/.virtualenvs/bagogold/bin/python
# -*- coding: utf-8 -*-
# Chamado no pretxncommit
"""Roda o pylint nos arquivos .py alterados"""
from pylint.lint import Run
from django.core.management import call_command
import os

print 'rodar pylint', os.environ["VIRTUAL_ENV"]
changed_files = [os.path.abspath(file) for file in repo[_node].changeset()[3]]
print changed_files

for change in [changed_file for changed_file in changed_files if '.py' in changed_file]:
  print change
  print Run(['--errors-only', change]) 
# TODO verificar erros
        
