# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0008_auto_20150926_0001'),
    ]

    operations = [
        migrations.CreateModel(
            name='FII',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ticker', models.CharField(max_length=10, verbose_name='Ticker da a\xe7\xe3o')),
            ],
        ),
        migrations.CreateModel(
            name='OperacaoFII',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('preco_unitario', models.DecimalField(verbose_name='Pre\xe7o unit\xe1rio', max_digits=11, decimal_places=2)),
                ('quantidade', models.IntegerField(verbose_name='Quantidade')),
                ('data', models.DateField(verbose_name='Data', blank=True)),
                ('corretagem', models.DecimalField(verbose_name='Corretagem', max_digits=11, decimal_places=2)),
                ('emolumentos', models.DecimalField(verbose_name='Emolumentos', max_digits=11, decimal_places=2)),
                ('tipo_operacao', models.CharField(max_length=1, verbose_name='Tipo de opera\xe7\xe3o')),
                ('consolidada', models.NullBooleanField(verbose_name='Consolidada?')),
                ('fii', models.ForeignKey(to='bagogold.FII')),
            ],
        ),
        migrations.CreateModel(
            name='ProventoFII',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('valor_unitario', models.DecimalField(verbose_name='Valor unit\xe1rio', max_digits=11, decimal_places=7)),
                ('tipo_provento', models.CharField(max_length=1, verbose_name='Tipo de provento')),
                ('data_ex', models.DateField(verbose_name='Data EX')),
                ('data_pagamento', models.DateField(verbose_name='Data do pagamento')),
                ('acao', models.ForeignKey(to='bagogold.Acao')),
            ],
        ),
    ]
