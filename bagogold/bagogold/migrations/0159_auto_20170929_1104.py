# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-09-29 14:04
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0158_divisaoinvestimento_quantidade'),
    ]

    operations = [
        migrations.DeleteModel(
            name='CarregamentoMetronic',
        ),
        migrations.RemoveField(
            model_name='cdb_rdb',
            name='investidor',
        ),
        migrations.RemoveField(
            model_name='historicocarenciacdb_rdb',
            name='cdb_rdb',
        ),
        migrations.RemoveField(
            model_name='historicoporcentagemcdb_rdb',
            name='cdb_rdb',
        ),
        migrations.RemoveField(
            model_name='historicovalorminimoinvestimentocdb_rdb',
            name='cdb_rdb',
        ),
        migrations.RemoveField(
            model_name='operacaocdb_rdb',
            name='investidor',
        ),
        migrations.RemoveField(
            model_name='operacaocdb_rdb',
            name='investimento',
        ),
        migrations.AlterUniqueTogether(
            name='operacaovendacdb_rdb',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='operacaovendacdb_rdb',
            name='operacao_compra',
        ),
        migrations.RemoveField(
            model_name='operacaovendacdb_rdb',
            name='operacao_venda',
        ),
        migrations.DeleteModel(
            name='CDB_RDB',
        ),
        migrations.DeleteModel(
            name='HistoricoCarenciaCDB_RDB',
        ),
        migrations.DeleteModel(
            name='HistoricoPorcentagemCDB_RDB',
        ),
        migrations.DeleteModel(
            name='HistoricoValorMinimoInvestimentoCDB_RDB',
        ),
        migrations.DeleteModel(
            name='OperacaoCDB_RDB',
        ),
        migrations.DeleteModel(
            name='OperacaoVendaCDB_RDB',
        ),
    ]