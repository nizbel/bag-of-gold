# -*- coding: utf-8 -*-
from bagogold.models.acoes import TaxaCustodiaAcao
from django import forms
from django.forms import widgets

ESCOLHAS_MES=((1,'Janeiro'), (2,'Fevereiro'),
          (3,'Março'), (4,'Abril'),
          (5,'Maio'), (6,'Junho'),
          (7,'Julho'), (8,'Agosto'),
          (9,'Setembro'), (10,'Outubro'),
          (11,'Novembro'), (12,'Dezembro'),)

class TaxaCustodiaAcaoForm(forms.ModelForm):

    class Meta:
        model = TaxaCustodiaAcao
        fields = ('valor_mensal', 'ano_vigencia', 'mes_vigencia')
        widgets={'mes_vigencia': widgets.Select(choices=ESCOLHAS_MES),}
