# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0024_acaoprovento'),
    ]

    operations = [
        migrations.AlterField(
            model_name='acaoprovento',
            name='data_pagamento_frac',
            field=models.DateField(verbose_name='Data do pagamento de fra\xe7\xf5es', blank=True),
        ),
        migrations.AlterField(
            model_name='acaoprovento',
            name='valor_calculo_frac',
            field=models.DecimalField(default=0, verbose_name='Valor para c\xe1lculo das fra\xe7\xf5es', max_digits=14, decimal_places=10),
        ),
        migrations.AlterField(
            model_name='provento',
            name='valor_unitario',
            field=models.DecimalField(verbose_name='Valor unit\xe1rio', max_digits=14, decimal_places=10),
        ),
    ]
