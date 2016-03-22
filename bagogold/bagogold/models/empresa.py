# -*- coding: utf-8 -*-
from django.db import models
 
class Empresa (models.Model):
    nome = models.CharField('Nome da empresa', max_length=100)