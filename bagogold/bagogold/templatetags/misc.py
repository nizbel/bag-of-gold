# -*- coding: utf-8 -*-
from bagogold.bagogold.utils.misc import \
    formatar_zeros_a_direita_apos_2_casas_decimais
from decimal import Decimal
from django import template

register = template.Library()

@register.filter
def dict_index(Dict, index):
    return Dict[index]

@register.filter
def template_abs(value):
    return abs(value)

@register.filter
def casas_decimais(value):
    return Decimal(formatar_zeros_a_direita_apos_2_casas_decimais(value))
