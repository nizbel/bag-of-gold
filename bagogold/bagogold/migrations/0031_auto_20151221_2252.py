# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0030_taxacustodiaacao'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='taxacustodiaacao',
            name='data_vigencia',
        ),
        migrations.AddField(
            model_name='taxacustodiaacao',
            name='ano_vigencia',
            field=models.IntegerField(default=None, verbose_name='Ano de in\xedcio de vig\xeancia'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='taxacustodiaacao',
            name='mes_vigencia',
            field=models.IntegerField(default=None, verbose_name='M\xeas de in\xedcio de vig\xeancia'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='taxacustodiaacao',
            name='valor_mensal',
            field=models.DecimalField(verbose_name='Valor mensal', max_digits=11, decimal_places=2),
        ),
    ]
