# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2017-04-29 20:03
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0144_auto_20170323_2029'),
    ]

    operations = [
        migrations.AlterField(
            model_name='acaoprovento',
            name='acao_recebida',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.Acao', verbose_name=b'A\xc3\xa7\xc3\xa3o'),
        ),
        migrations.AlterField(
            model_name='historicoacao',
            name='acao',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.Acao', unique_for_date=b'data', verbose_name=b'A\xc3\xa7\xc3\xa3o'),
        ),
        migrations.AlterField(
            model_name='operacaoacao',
            name='acao',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.Acao', verbose_name=b'A\xc3\xa7\xc3\xa3o'),
        ),
        migrations.AlterField(
            model_name='operacaocompravenda',
            name='compra',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='compra', to='bagogold.OperacaoAcao', verbose_name=b'Compra'),
        ),
        migrations.AlterField(
            model_name='operacaocompravenda',
            name='venda',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='venda', to='bagogold.OperacaoAcao', verbose_name=b'Venda'),
        ),
        migrations.AlterField(
            model_name='operacaoletracredito',
            name='letra_credito',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.LetraCredito', verbose_name=b'Letra de Cr\xc3\xa9dito'),
        ),
        migrations.AlterField(
            model_name='provento',
            name='acao',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.Acao', verbose_name=b'A\xc3\xa7\xc3\xa3o'),
        ),
        migrations.AlterField(
            model_name='usoproventosoperacaoacao',
            name='operacao',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.OperacaoAcao', verbose_name=b'Opera\xc3\xa7\xc3\xa3o'),
        ),
        migrations.AlterField(
            model_name='valordiarioacao',
            name='acao',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.Acao', verbose_name=b'A\xc3\xa7\xc3\xa3o'),
        ),
    ]
