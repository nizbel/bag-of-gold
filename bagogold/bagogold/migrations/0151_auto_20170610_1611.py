# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-10 19:11
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0150_auto_20170608_2331'),
        ('fundo_investimento', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='divisaooperacaofundoinvestimento',
            name='operacao',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fundo_investimento.OperacaoFundoInvestimento'),
        ),
    ]
