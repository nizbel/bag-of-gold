# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-04-24 04:43
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0178_auto_20180422_2130'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='historicocarencialetracredito',
            name='letra_credito',
        ),
        migrations.RemoveField(
            model_name='historicoporcentagemletracredito',
            name='letra_credito',
        ),
        migrations.RemoveField(
            model_name='historicovalorminimoinvestimento',
            name='letra_credito',
        ),
        migrations.RemoveField(
            model_name='letracredito',
            name='investidor',
        ),
        migrations.RemoveField(
            model_name='operacaoletracredito',
            name='investidor',
        ),
        migrations.RemoveField(
            model_name='operacaoletracredito',
            name='letra_credito',
        ),
        migrations.AlterUniqueTogether(
            name='operacaovendaletracredito',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='operacaovendaletracredito',
            name='operacao_compra',
        ),
        migrations.RemoveField(
            model_name='operacaovendaletracredito',
            name='operacao_venda',
        ),
        migrations.DeleteModel(
            name='HistoricoCarenciaLetraCredito',
        ),
        migrations.DeleteModel(
            name='HistoricoPorcentagemLetraCredito',
        ),
        migrations.DeleteModel(
            name='HistoricoValorMinimoInvestimento',
        ),
        migrations.DeleteModel(
            name='LetraCredito',
        ),
        migrations.DeleteModel(
            name='OperacaoLetraCredito',
        ),
        migrations.DeleteModel(
            name='OperacaoVendaLetraCredito',
        ),
    ]
