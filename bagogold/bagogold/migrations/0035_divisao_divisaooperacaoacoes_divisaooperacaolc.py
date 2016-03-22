# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0034_auto_20151223_0057'),
    ]

    operations = [
        migrations.CreateModel(
            name='Divisao',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome', models.CharField(max_length=50, verbose_name='Nome da divis\xe3o')),
                ('valor_objetivo', models.DecimalField(verbose_name='Objetivo', max_digits=11, decimal_places=2, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='DivisaoOperacaoAcoes',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('divisao', models.ForeignKey(to='bagogold.Divisao')),
                ('operacao', models.ForeignKey(to='bagogold.OperacaoAcao')),
            ],
        ),
        migrations.CreateModel(
            name='DivisaoOperacaoLC',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('quantidade', models.DecimalField(verbose_name=b'Quantidade', max_digits=11, decimal_places=2)),
                ('divisao', models.ForeignKey(to='bagogold.Divisao')),
                ('operacao', models.ForeignKey(to='bagogold.OperacaoLetraCredito')),
            ],
        ),
    ]
