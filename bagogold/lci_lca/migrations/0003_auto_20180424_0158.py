# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2018-04-24 04:58
from __future__ import unicode_literals

from decimal import Decimal
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lci_lca', '0002_historicovencimentoletracredito'),
    ]

    operations = [
        migrations.CreateModel(
            name='CheckpointCDB_RDB',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ano', models.SmallIntegerField(verbose_name='Ano')),
                ('qtd_restante', models.DecimalField(decimal_places=2, max_digits=11, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))], verbose_name='Quantidade restante da opera\xe7\xe3o')),
                ('qtd_atualizada', models.DecimalField(decimal_places=8, max_digits=17, validators=[django.core.validators.MinValueValidator(Decimal('1E-8'))], verbose_name='Quantidade atualizada da opera\xe7\xe3o')),
                ('operacao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lci_lca.OperacaoLetraCredito')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='checkpointcdb_rdb',
            unique_together=set([('operacao', 'ano')]),
        ),
    ]