# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-04-17 07:24
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0176_auto_20180322_1516'),
        ('tesouro_direto', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='divisaooperacaotd',
            name='operacao',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tesouro_direto.OperacaoTitulo'),
        ),
    ]