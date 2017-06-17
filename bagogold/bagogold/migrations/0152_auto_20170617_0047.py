# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-17 03:47
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0151_auto_20170610_1611'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='fundoinvestimento',
            name='investidor',
        ),
        migrations.RemoveField(
            model_name='historicocarenciafundoinvestimento',
            name='fundo_investimento',
        ),
        migrations.RemoveField(
            model_name='historicovalorcotas',
            name='fundo_investimento',
        ),
        migrations.RemoveField(
            model_name='historicovalorminimoinvestimentofundoinvestimento',
            name='fundo_investimento',
        ),
        migrations.RemoveField(
            model_name='operacaofundoinvestimento',
            name='fundo_investimento',
        ),
        migrations.RemoveField(
            model_name='operacaofundoinvestimento',
            name='investidor',
        ),
        migrations.DeleteModel(
            name='FundoInvestimento',
        ),
        migrations.DeleteModel(
            name='HistoricoCarenciaFundoInvestimento',
        ),
        migrations.DeleteModel(
            name='HistoricoValorCotas',
        ),
        migrations.DeleteModel(
            name='HistoricoValorMinimoInvestimentoFundoInvestimento',
        ),
        migrations.DeleteModel(
            name='OperacaoFundoInvestimento',
        ),
    ]