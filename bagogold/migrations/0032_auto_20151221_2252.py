# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0031_auto_20151221_2252'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricoCarenciaLetraCredito',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('carencia', models.IntegerField(verbose_name='Per\xedodo de car\xeancia')),
                ('data', models.DateField(verbose_name='Data da varia\xe7\xe3o')),
            ],
        ),
        migrations.CreateModel(
            name='HistoricoPorcentagemLetraCredito',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('porcentagem_di', models.DecimalField(verbose_name='Porcentagem do DI', max_digits=5, decimal_places=2)),
                ('data', models.DateField(verbose_name='Data da varia\xe7\xe3o')),
            ],
        ),
        migrations.CreateModel(
            name='HistoricoTaxaDI',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('data', models.DateField(verbose_name='Data')),
                ('taxa', models.DecimalField(verbose_name='Rendimento anual', max_digits=5, decimal_places=2)),
            ],
        ),
        migrations.CreateModel(
            name='LetraCredito',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome', models.CharField(max_length=50, verbose_name='Nome')),
            ],
        ),
        migrations.CreateModel(
            name='OperacaoLetraCredito',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('quantidade', models.DecimalField(verbose_name='Quantidade investida', max_digits=11, decimal_places=2)),
                ('data', models.DateField(verbose_name='Data da opera\xe7\xe3o')),
                ('tipo_operacao', models.CharField(max_length=1, verbose_name='Tipo de opera\xe7\xe3o')),
                ('letra_credito', models.ForeignKey(to='bagogold.LetraCredito')),
            ],
        ),
        migrations.AddField(
            model_name='historicoporcentagemletracredito',
            name='letra_credito',
            field=models.ForeignKey(to='bagogold.LetraCredito'),
        ),
        migrations.AddField(
            model_name='historicocarencialetracredito',
            name='letra_credito',
            field=models.ForeignKey(to='bagogold.LetraCredito'),
        ),
    ]
