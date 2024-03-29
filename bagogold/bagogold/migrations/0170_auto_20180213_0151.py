# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-02-13 03:51
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0169_auto_20180206_1910'),
        ('fii', '0002_auto_20180212_2018'),
        ('lci_lca', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='checkpointdivisaofii',
            name='fii',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fii.FII'),
        ),
        migrations.AlterField(
            model_name='divisaooperacaofii',
            name='operacao',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fii.OperacaoFII'),
        ),
        migrations.AlterField(
            model_name='divisaooperacaolc',
            name='operacao',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lci_lca.OperacaoLetraCredito'),
        ),
        migrations.AlterField(
            model_name='proventofiidescritodocumentobovespa',
            name='fii',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fii.FII'),
        ),
        migrations.AlterField(
            model_name='proventofiidocumento',
            name='provento',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='fii.ProventoFII'),
        ),
    ]
