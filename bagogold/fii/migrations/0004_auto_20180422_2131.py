# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-04-23 00:31
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fii', '0003_auto_20180213_1424'),
    ]

    operations = [
        migrations.AlterField(
            model_name='checkpointfii',
            name='investidor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.Investidor'),
        ),
        migrations.AlterField(
            model_name='checkpointproventosfii',
            name='investidor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.Investidor'),
        ),
        migrations.AlterField(
            model_name='fii',
            name='empresa',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='bagogold.Empresa'),
        ),
        migrations.AlterField(
            model_name='operacaofii',
            name='investidor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.Investidor'),
        ),
        migrations.AlterField(
            model_name='usoproventosoperacaofii',
            name='divisao_operacao',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='bagogold.DivisaoOperacaoFII'),
        ),
    ]
