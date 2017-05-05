# -*- coding: utf-8 -*-
from django.contrib import admin
from bagogold.cri_cra.models.cri_cra import CRI_CRA, DataRemuneracaoCRI_CRA,\
    DataAmortizacaoCRI_CRA, OperacaoCRI_CRA

admin.site.register(CRI_CRA)
    
admin.site.register(OperacaoCRI_CRA)
    
admin.site.register(DataRemuneracaoCRI_CRA)
    
admin.site.register(DataAmortizacaoCRI_CRA)
    
