# -*- coding: utf-8 -*-
from django import template

register = template.Library()

@register.filter
def dict_index(Dict, index):
    return Dict[index]

@register.filter
def template_abs(value):
    return abs(value)