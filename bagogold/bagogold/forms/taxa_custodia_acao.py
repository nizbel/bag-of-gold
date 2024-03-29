# -*- coding: utf-8 -*-
from bagogold.bagogold.forms.utils import LocalizedModelForm
from bagogold.bagogold.models.acoes import TaxaCustodiaAcao
from django import forms
from django.forms import widgets

ESCOLHAS_MES=((1,'Janeiro'), (2,'Fevereiro'),
          (3,'Março'), (4,'Abril'),
          (5,'Maio'), (6,'Junho'),
          (7,'Julho'), (8,'Agosto'),
          (9,'Setembro'), (10,'Outubro'),
          (11,'Novembro'), (12,'Dezembro'),)

class TaxaCustodiaAcaoForm(LocalizedModelForm):

    class Meta:
        model = TaxaCustodiaAcao
        fields = ('valor_mensal', 'ano_vigencia', 'mes_vigencia')
        widgets={'mes_vigencia': widgets.Select(choices=ESCOLHAS_MES),}
