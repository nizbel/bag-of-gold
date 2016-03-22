# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Operacao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('day_trade', models.NullBooleanField(default=False, verbose_name=b'\xc3\x89 day trade?')),
            ],
        ),
        migrations.CreateModel(
            name='OperacaoAcao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('preco_unitario', models.DecimalField(verbose_name=b'Pre\xc3\xa7o unit\xc3\xa1rio', max_digits=11, decimal_places=2)),
                ('data', models.DateField(verbose_name=b'Data')),
                ('corretagem', models.DecimalField(verbose_name=b'Corretagem', max_digits=11, decimal_places=2)),
                ('emolumentos', models.DecimalField(verbose_name=b'Emolumentos', max_digits=11, decimal_places=2)),
                ('tipo_operacao', models.CharField(max_length=1, verbose_name=b'Tipo de opera\xc3\xa7\xc3\xa3o')),
                ('consolidada', models.NullBooleanField(verbose_name=b'Consolidada?')),
                ('acao', models.ForeignKey(to='bagogold.Acao')),
            ],
        ),
        migrations.CreateModel(
            name='Provento',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('valor_unitario', models.DecimalField(verbose_name=b'Valor unit\xc3\xa1rio', max_digits=11, decimal_places=7)),
                ('tipo_provento', models.CharField(max_length=1, verbose_name=b'Tipo de provento')),
                ('data_ex', models.DateField(verbose_name=b'Data EX')),
                ('data_pagamento', models.DateField(verbose_name=b'Data do pagamento')),
                ('acao', models.ForeignKey(to='bagogold.Acao')),
            ],
        ),
        migrations.AddField(
            model_name='operacao',
            name='compra',
            field=models.ForeignKey(related_name='compra', to='bagogold.OperacaoAcao'),
        ),
        migrations.AddField(
            model_name='operacao',
            name='venda',
            field=models.ForeignKey(related_name='venda', to='bagogold.OperacaoAcao'),
        ),
    ]
