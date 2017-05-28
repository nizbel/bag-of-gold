# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-11-06 01:52
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0088_auto_20161105_2343'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='proventoacaodescritodocumentobovespa',
            name='documento',
        ),
        migrations.RemoveField(
            model_name='proventofiidescritodocumentobovespa',
            name='documento',
        ),
        migrations.AddField(
            model_name='proventoacaodocumento',
            name='descricao_provento',
            field=models.OneToOneField(default=None, on_delete=django.db.models.deletion.CASCADE, to='bagogold.ProventoAcaoDescritoDocumentoBovespa'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='proventofiidocumento',
            name='descricao_provento',
            field=models.OneToOneField(default=None, on_delete=django.db.models.deletion.CASCADE, to='bagogold.ProventoFIIDescritoDocumentoBovespa'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='proventoacaodocumento',
            name='provento',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='bagogold.Provento'),
        ),
        migrations.AlterField(
            model_name='proventofiidocumento',
            name='provento',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='bagogold.ProventoFII'),
        ),
    ]
