# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-07-05 02:44
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('criptomoeda', '0006_auto_20170823_0335'),
        ('bagogold', '0153_atualizacaoselicprovento'),
    ]

    operations = [
        migrations.CreateModel(
            name='SelicProventoAcaoDescritoDocBovespa',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_inicio', models.DateField(verbose_name='Data de \xednicio')),
                ('data_fim', models.DateField(verbose_name='Data de fim')),
                ('provento', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='bagogold.Provento')),
            ],
        ),
        migrations.CreateModel(
            name='DivisaoTransferenciaCriptomoeda',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantidade', models.DecimalField(decimal_places=12, max_digits=21, verbose_name=b'Quantidade')),
                ('divisao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.Divisao', verbose_name='Divis\xe3o')),
                ('transferencia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='criptomoeda.TransferenciaCriptomoeda')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='divisaotransferenciacriptomoeda',
            unique_together=set([('divisao', 'transferencia')]),
        ),
    ]
