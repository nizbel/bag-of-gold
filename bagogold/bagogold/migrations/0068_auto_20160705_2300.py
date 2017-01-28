# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-07-06 02:00
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bagogold', '0067_historicoipca'),
    ]

    operations = [
        migrations.CreateModel(
            name='DivisaoOperacaoFundoInvestimento',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantidade', models.DecimalField(decimal_places=2, max_digits=11, verbose_name=b'Quantidade')),
                ('divisao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.Divisao')),
            ],
        ),
        migrations.CreateModel(
            name='FundoInvestimento',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=50, verbose_name='Nome')),
                ('descricao', models.CharField(max_length=200, verbose_name='Descri\xe7\xe3o')),
                ('tipo_prazo', models.CharField(max_length=1, verbose_name='Tipo de prazo')),
                ('investidor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.Investidor')),
            ],
        ),
        migrations.CreateModel(
            name='HistoricoCarenciaFundoInvestimento',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('carencia', models.IntegerField(verbose_name='Per\xedodo de car\xeancia')),
                ('data', models.DateField(blank=True, null=True, verbose_name='Data da varia\xe7\xe3o')),
                ('fundo_investimento', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.FundoInvestimento')),
            ],
        ),
        migrations.CreateModel(
            name='HistoricoValorCotas',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.DateField(verbose_name='Data da opera\xe7\xe3o')),
                ('valor_cota', models.DecimalField(decimal_places=2, max_digits=11, verbose_name='Quantidade de cotas')),
                ('fundo_investimento', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.FundoInvestimento')),
            ],
        ),
        migrations.CreateModel(
            name='HistoricoValorMinimoInvestimentoFundoInvestimento',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('valor_minimo', models.DecimalField(decimal_places=2, max_digits=9, verbose_name='Valor m\xednimo para investimento')),
                ('data', models.DateField(blank=True, null=True, verbose_name='Data da varia\xe7\xe3o')),
                ('fundo_investimento', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.FundoInvestimento')),
            ],
        ),
        migrations.CreateModel(
            name='OperacaoFundoInvestimento',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantidade_cotas', models.DecimalField(decimal_places=2, max_digits=11, verbose_name='Quantidade de cotas')),
                ('valor', models.DecimalField(decimal_places=2, max_digits=11, verbose_name='Valor da opera\xe7\xe3o')),
                ('data', models.DateField(verbose_name='Data da opera\xe7\xe3o')),
                ('tipo_operacao', models.CharField(max_length=1, verbose_name='Tipo de opera\xe7\xe3o')),
                ('fundo_investimento', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.FundoInvestimento')),
                ('investidor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.Investidor')),
            ],
        ),
        migrations.AddField(
            model_name='divisaooperacaofundoinvestimento',
            name='operacao',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bagogold.OperacaoFundoInvestimento'),
        ),
        migrations.AlterUniqueTogether(
            name='divisaooperacaofundoinvestimento',
            unique_together=set([('divisao', 'operacao')]),
        ),
    ]
