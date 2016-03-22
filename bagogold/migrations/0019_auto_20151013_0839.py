# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0018_auto_20151010_2352'),
    ]

    operations = [
        migrations.AlterField(
            model_name='operacaotitulo',
            name='quantidade',
            field=models.DecimalField(verbose_name='Quantidade', max_digits=7, decimal_places=2),
        ),
    ]
