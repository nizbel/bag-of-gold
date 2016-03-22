# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0033_auto_20151222_0018'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historicocarencialetracredito',
            name='data',
            field=models.DateField(verbose_name='Data da varia\xe7\xe3o', blank=True),
        ),
        migrations.AlterField(
            model_name='historicoporcentagemletracredito',
            name='data',
            field=models.DateField(verbose_name='Data da varia\xe7\xe3o', blank=True),
        ),
    ]
