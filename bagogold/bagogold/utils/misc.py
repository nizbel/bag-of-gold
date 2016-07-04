# -*- coding: utf-8 -*-
import math

def calcular_iof_regressivo(dias):
   return max((100 - (dias * 3 + math.ceil((float(dias)/3)))), 0)/100