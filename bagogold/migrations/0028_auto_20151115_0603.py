# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0027_auto_20151031_1440'),
    ]

    operations = [
        migrations.AlterField(
            model_name='provento',
            name='valor_unitario',
            field=models.DecimalField(verbose_name='Valor unit\xe1rio', max_digits=16, decimal_places=12),
        ),
        migrations.AlterField(
            model_name='usoproventosoperacaoacao',
            name='qtd_utilizada',
            field=models.DecimalField(verbose_name='Quantidade de proventos utilizada', max_digits=11, decimal_places=2),
        ),
    ]
