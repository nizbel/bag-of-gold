# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-02-13 03:31
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('bagogold', '0169_auto_20180206_1910'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricoCarenciaLetraCredito',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('carencia', models.IntegerField(verbose_name='Per\xedodo de car\xeancia')),
                ('data', models.DateField(blank=True, null=True, verbose_name='Data da varia\xe7\xe3o')),
            ],
        ),
        migrations.CreateModel(
            name='HistoricoPorcentagemLetraCredito',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('porcentagem_di', models.DecimalField(decimal_places=2, max_digits=5, verbose_name='Porcentagem do DI')),
                ('data', models.DateField(blank=True, null=True, verbose_name='Data da varia\xe7\xe3o')),
            ],
        ),
        migrations.CreateModel(
            name='HistoricoValorMinimoInvestimento',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('valor_minimo', models.DecimalField(decimal_places=2, max_digits=9, verbose_name='Valor m\xednimo para investimento')),
                ('data', models.DateField(blank=True, null=True, verbose_name='Data da varia\xe7\xe3o')),
            ],
        ),
        migrations.CreateModel(
            name='LetraCredito',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=50, verbose_name='Nome')),
                ('investidor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lci_lca_novo', to='bagogold.Investidor')),
            ],
        ),
        migrations.CreateModel(
            name='OperacaoLetraCredito',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantidade', models.DecimalField(decimal_places=2, max_digits=11, verbose_name='Quantidade investida/resgatada')),
                ('data', models.DateField(verbose_name='Data da opera\xe7\xe3o')),
                ('tipo_operacao', models.CharField(max_length=1, verbose_name='Tipo de opera\xe7\xe3o')),
                ('investidor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='op_lci_lca_novo', to='bagogold.Investidor')),
                ('letra_credito', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lci_lca.LetraCredito', verbose_name=b'Letra de Cr\xc3\xa9dito')),
            ],
        ),
        migrations.CreateModel(
            name='OperacaoVendaLetraCredito',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('operacao_compra', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='operacao_compra', to='lci_lca.OperacaoLetraCredito')),
                ('operacao_venda', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='operacao_venda', to='lci_lca.OperacaoLetraCredito')),
            ],
        ),
        migrations.AddField(
            model_name='historicovalorminimoinvestimento',
            name='letra_credito',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lci_lca.LetraCredito'),
        ),
        migrations.AddField(
            model_name='historicoporcentagemletracredito',
            name='letra_credito',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lci_lca.LetraCredito'),
        ),
        migrations.AddField(
            model_name='historicocarencialetracredito',
            name='letra_credito',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lci_lca.LetraCredito'),
        ),
        migrations.AlterUniqueTogether(
            name='operacaovendaletracredito',
            unique_together=set([('operacao_compra', 'operacao_venda')]),
        ),
    ]
