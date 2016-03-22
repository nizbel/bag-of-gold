# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0003_operacaoacao_quantidade'),
    ]

    operations = [
        migrations.AlterField(
            model_name='acao',
            name='ticker',
            field=models.CharField(max_length=10, verbose_name='Ticker da a\xe7\xe3o'),
        ),
        migrations.AlterField(
            model_name='operacao',
            name='day_trade',
            field=models.NullBooleanField(default=False, verbose_name='\xc9 day trade?'),
        ),
        migrations.AlterField(
            model_name='operacaoacao',
            name='data',
            field=models.DateField(verbose_name='Data', blank=True),
        ),
        migrations.AlterField(
            model_name='operacaoacao',
            name='preco_unitario',
            field=models.DecimalField(verbose_name='Pre\xe7o unit\xe1rio', max_digits=11, decimal_places=2),
        ),
        migrations.AlterField(
            model_name='operacaoacao',
            name='tipo_operacao',
            field=models.CharField(max_length=1, verbose_name='Tipo de opera\xe7\xe3o'),
        ),
        migrations.AlterField(
            model_name='provento',
            name='valor_unitario',
            field=models.DecimalField(verbose_name='Valor unit\xe1rio', max_digits=11, decimal_places=7),
        ),
    ]
