# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-25 19:54
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('criptomoeda', '0002_auto_20170818_1510'),
        ('bagogold', '0152_auto_20170617_0047'),
    ]

    operations = [
        migrations.CreateModel(
            name='AtualizacaoSelicProvento',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('valor_rendimento', models.DecimalField(blank=True, decimal_places=15, max_digits=19, null=True, verbose_name='Valor do rendimento')),
                ('data_inicio', models.DateField(verbose_name='Data de \xednicio')),
                ('data_fim', models.DateField(verbose_name='Data de fim')),
                ('provento', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='bagogold.Provento')),
            ],
        ),
        migrations.CreateModel(
            name='DivisaoOperacaoCriptomoeda',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantidade', models.DecimalField(decimal_places=12, max_digits=21, verbose_name=b'Quantidade')),
                ('divisao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.Divisao', verbose_name='Divis\xe3o')),
                ('operacao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='criptomoeda.OperacaoCriptomoeda')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='divisaooperacaocriptomoeda',
            unique_together=set([('divisao', 'operacao')]),
        ),
    ]
